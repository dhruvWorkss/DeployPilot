from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import User, operator
from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .incident import analyze_logs
from .models import AuditEvent, Deployment, DeploymentStatus, Incident, Service
from .schemas import (
    DeploymentCreate,
    DeploymentOut,
    IncidentAnalyze,
    IncidentOut,
    Overview,
    ServiceOut,
)

REQUESTS = Counter("deploypilot_api_requests_total", "API mutations", ["operation", "result"])


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count(Service.id))):
            return
        services = [
            Service(
                name="checkout-api",
                repository="github.com/acme/checkout",
                owner="payments",
                health="healthy",
            ),
            Service(
                name="catalog",
                repository="github.com/acme/catalog",
                owner="commerce",
                health="healthy",
            ),
            Service(
                name="notification-worker",
                repository="github.com/acme/notifications",
                owner="platform",
                health="degraded",
            ),
        ]
        db.add_all(services)
        db.flush()
        db.add_all(
            [
                Deployment(
                    service_id=services[0].id,
                    version="v2.14.3",
                    commit_sha="8f17a2c",
                    image="registry/checkout@sha256:demo",
                    status=DeploymentStatus.healthy,
                    actor="maya@acme.io",
                    duration_seconds=184,
                    finished_at=datetime.now(UTC) - timedelta(minutes=18),
                ),
                Deployment(
                    service_id=services[1].id,
                    version="v4.8.1",
                    commit_sha="c3e791a",
                    image="registry/catalog@sha256:demo",
                    status=DeploymentStatus.healthy,
                    actor="jenkins",
                    duration_seconds=132,
                    finished_at=datetime.now(UTC) - timedelta(hours=2),
                ),
                Deployment(
                    service_id=services[2].id,
                    version="v1.9.0",
                    commit_sha="a44ed10",
                    image="registry/notify@sha256:demo",
                    status=DeploymentStatus.rolled_back,
                    actor="jenkins",
                    duration_seconds=96,
                    finished_at=datetime.now(UTC) - timedelta(hours=4),
                ),
            ]
        )
        db.add(
            Incident(
                service_id=services[2].id,
                title="Readiness probe failure after v1.9.0",
                category="readiness",
                severity="high",
                confidence="high",
                evidence=["readiness probe failed"],
                recommendations=[
                    "Inspect the readiness dependency check.",
                    "Compare configuration with the previous revision.",
                ],
            )
        )
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    if get_settings().environment == "development":
        seed()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/services", response_model=list[ServiceOut])
def services(db: Session = Depends(get_db)):
    return db.scalars(select(Service).order_by(Service.name)).all()


@app.get("/api/v1/deployments", response_model=list[DeploymentOut])
def deployments(limit: int = 20, db: Session = Depends(get_db)):
    return db.scalars(
        select(Deployment).order_by(Deployment.started_at.desc()).limit(min(limit, 100))
    ).all()


@app.post("/api/v1/deployments", response_model=DeploymentOut, status_code=status.HTTP_202_ACCEPTED)
def create_deployment(
    payload: DeploymentCreate, db: Session = Depends(get_db), user: User = Depends(operator)
):
    if not db.get(Service, payload.service_id):
        raise HTTPException(404, "Service not found")
    deployment = Deployment(
        **payload.model_dump(), status=DeploymentStatus.queued, actor=user.subject
    )
    db.add(deployment)
    db.flush()
    db.add(
        AuditEvent(
            actor=user.subject,
            action="deployment.created",
            resource_type="deployment",
            resource_id=deployment.id,
            detail=f"Release {payload.version} queued",
        )
    )
    db.commit()
    REQUESTS.labels("create_deployment", "accepted").inc()
    return deployment


@app.post("/api/v1/deployments/{deployment_id}/rollback", response_model=DeploymentOut)
def rollback(deployment_id: str, db: Session = Depends(get_db), user: User = Depends(operator)):
    deployment = db.get(Deployment, deployment_id)
    if not deployment:
        raise HTTPException(404, "Deployment not found")
    deployment.status = DeploymentStatus.rolled_back
    deployment.finished_at = datetime.now(UTC)
    db.add(
        AuditEvent(
            actor=user.subject,
            action="deployment.rollback",
            resource_type="deployment",
            resource_id=deployment.id,
            detail="Manual rollback requested",
        )
    )
    db.commit()
    REQUESTS.labels("rollback", "accepted").inc()
    return deployment


@app.get("/api/v1/incidents", response_model=list[IncidentOut])
def incidents(db: Session = Depends(get_db)):
    return db.scalars(select(Incident).order_by(Incident.created_at.desc()).limit(100)).all()


@app.post("/api/v1/incidents/analyze", response_model=IncidentOut)
def analyze(
    payload: IncidentAnalyze, db: Session = Depends(get_db), user: User = Depends(operator)
):
    result = analyze_logs(payload.logs)
    incident = Incident(service_id=payload.service_id, **result)
    db.add(incident)
    db.flush()
    db.add(
        AuditEvent(
            actor=user.subject,
            action="incident.analyzed",
            resource_type="incident",
            resource_id=incident.id,
            detail=str(result["category"]),
        )
    )
    db.commit()
    return incident


@app.get("/api/v1/overview", response_model=Overview)
def overview(db: Session = Depends(get_db)):
    service_count = db.scalar(select(func.count(Service.id))) or 0
    healthy_count = (
        db.scalar(select(func.count(Service.id)).where(Service.health == "healthy")) or 0
    )
    day_start = datetime.now(UTC) - timedelta(days=1)
    deployments_today = (
        db.scalar(select(func.count(Deployment.id)).where(Deployment.started_at >= day_start)) or 0
    )
    successful = (
        db.scalar(
            select(func.count(Deployment.id)).where(Deployment.status == DeploymentStatus.healthy)
        )
        or 0
    )
    total = db.scalar(select(func.count(Deployment.id))) or 0
    open_incidents = (
        db.scalar(select(func.count(Incident.id)).where(Incident.status == "open")) or 0
    )
    recent = db.scalars(select(Deployment).order_by(Deployment.started_at.desc()).limit(6)).all()
    return Overview(
        services=service_count,
        healthy_services=healthy_count,
        deployments_today=deployments_today,
        success_rate=round(successful / total * 100, 1) if total else 100,
        open_incidents=open_incidents,
        recent_deployments=recent,
    )
