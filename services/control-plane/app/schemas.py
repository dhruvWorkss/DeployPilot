from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import DeploymentStatus


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ServiceOut(APIModel):
    id: str
    name: str
    repository: str
    environment: str
    health: str
    owner: str
    created_at: datetime


class DeploymentCreate(BaseModel):
    service_id: str
    version: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    commit_sha: str = Field(min_length=7, max_length=40, pattern=r"^[a-fA-F0-9]+$")
    image: str = Field(min_length=3, max_length=255)


class DeploymentOut(APIModel):
    id: str
    service_id: str
    service_name: str
    version: str
    commit_sha: str
    image: str
    status: DeploymentStatus
    actor: str
    duration_seconds: int | None
    started_at: datetime
    finished_at: datetime | None


class IncidentAnalyze(BaseModel):
    logs: str = Field(min_length=3, max_length=200_000)
    service_id: str | None = None


class IncidentOut(APIModel):
    id: str
    service_id: str | None
    title: str
    category: str
    severity: str
    confidence: str
    status: str
    evidence: list[str]
    recommendations: list[str]
    created_at: datetime


class Overview(BaseModel):
    services: int
    healthy_services: int
    deployments_today: int
    success_rate: float
    open_incidents: int
    recent_deployments: list[DeploymentOut]
