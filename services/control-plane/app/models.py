import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now() -> datetime:
    return datetime.now(UTC)


class DeploymentStatus(str, enum.Enum):
    queued = "queued"
    building = "building"
    deploying = "deploying"
    verifying = "verifying"
    healthy = "healthy"
    failed = "failed"
    rolled_back = "rolled_back"


class Service(Base):
    __tablename__ = "services"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    repository: Mapped[str] = mapped_column(String(255))
    environment: Mapped[str] = mapped_column(String(40), default="production")
    health: Mapped[str] = mapped_column(String(30), default="healthy")
    owner: Mapped[str] = mapped_column(String(80), default="platform")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="service")


class Deployment(Base):
    __tablename__ = "deployments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id"), index=True)
    version: Mapped[str] = mapped_column(String(80))
    commit_sha: Mapped[str] = mapped_column(String(40))
    image: Mapped[str] = mapped_column(String(255))
    status: Mapped[DeploymentStatus] = mapped_column(Enum(DeploymentStatus))
    actor: Mapped[str] = mapped_column(String(120), default="system")
    duration_seconds: Mapped[int | None]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    service: Mapped[Service] = relationship(back_populates="deployments")

    @property
    def service_name(self) -> str:
        return self.service.name


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_id: Mapped[str | None] = mapped_column(ForeignKey("services.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(60))
    severity: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="open")
    evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(80))
    resource_type: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[str] = mapped_column(String(36))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
