"""Tests for health, readiness, request IDs, and observability."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import engine, Base


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoints:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_readiness_returns_ok(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert "request_id" in data

    def test_request_id_header_present(self, client):
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_request_id_generated_when_missing(self, client):
        response = client.get("/health")
        req_id = response.headers.get("X-Request-ID")
        assert req_id is not None
        assert len(req_id) > 0

    def test_request_id_preserved_when_provided(self, client):
        custom_id = "test-request-123"
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.headers["X-Request-ID"] == custom_id
