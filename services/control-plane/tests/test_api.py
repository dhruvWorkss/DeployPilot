from fastapi.testclient import TestClient

from app.main import app


def test_health_and_overview():
    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        response = client.get("/api/v1/overview")
        assert response.status_code == 200
        assert response.json()["services"] >= 3


def test_deployment_is_auditable_mutation():
    with TestClient(app) as client:
        service = client.get("/api/v1/services").json()[0]
        response = client.post(
            "/api/v1/deployments",
            json={
                "service_id": service["id"],
                "version": "v9.1.0",
                "commit_sha": "a12bc34",
                "image": "registry.example.com/service@sha256:abc",
            },
        )
        assert response.status_code == 202
        assert response.json()["status"] == "queued"


def test_incident_analysis_endpoint():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/incidents/analyze",
            json={"logs": "OOMKilled container exited with exit code 137"},
        )
        assert response.status_code == 200
        assert response.json()["category"] == "out_of_memory"
