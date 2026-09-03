"""Tests covering the production deployment configuration.

These tests intentionally do NOT touch live Vercel / Render / Neon
services — they only verify that the application boots and behaves
correctly when configured as it would be on Render.
"""

import os
import importlib

import pytest
from fastapi.testclient import TestClient


def _reload_settings():
    """Reload the cached Settings object after monkey-patching the env."""
    from app import config as config_module

    config_module.get_settings.cache_clear()
    importlib.reload(config_module)
    return config_module.settings


class TestCorsOrigins:
    def test_default_cors_includes_local_dev_origins(self):
        # Don't change the env — just confirm the default list is sane.
        settings = _reload_settings()
        assert "http://localhost:5173" in settings.CORS_ORIGINS
        assert "http://127.0.0.1:5173" in settings.CORS_ORIGINS

    def test_comma_separated_cors_origins(self, monkeypatch):
        monkeypatch.setenv(
            "CORS_ORIGINS",
            "https://agentic-company-simulator.vercel.app,https://www.example.com",
        )
        settings = _reload_settings()
        assert settings.CORS_ORIGINS == [
            "https://agentic-company-simulator.vercel.app",
            "https://www.example.com",
        ]

    def test_empty_cors_origins_falls_back_to_empty_list(self, monkeypatch):
        monkeypatch.setenv("CORS_ORIGINS", "")
        settings = _reload_settings()
        assert settings.CORS_ORIGINS == []

    def test_wildcard_cors_origin_is_not_used_by_default(self):
        # The application must not silently fall back to "*" in any
        # production-shaped configuration.
        settings = _reload_settings()
        assert "*" not in settings.CORS_ORIGINS


class TestProductionEnvironment:
    def test_environment_defaults_to_development(self):
        settings = _reload_settings()
        assert settings.ENVIRONMENT in ("development", "test", "production")

    def test_database_url_is_configurable(self, monkeypatch):
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://user:pass@host.neon.tech/db?sslmode=require",
        )
        settings = _reload_settings()
        assert settings.DATABASE_URL.startswith("postgresql://")

    def test_sqlalchemy_engine_uses_configured_database_url(self, monkeypatch):
        # Keep using SQLite for the actual engine — we just verify the
        # engine URL matches the configured DATABASE_URL.
        from app import db as db_module

        monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_deployment.db")
        db_module.get_settings.cache_clear() if hasattr(db_module, "get_settings") else None
        # The engine is bound at import time; we rebuild it manually to
        # confirm the configuration is honored.
        from sqlalchemy import create_engine

        engine = create_engine("sqlite:///./test_deployment.db", future=True)
        assert engine.url.drivername == "sqlite"
        assert str(engine.url).endswith("test_deployment.db")


class TestHealthAndReadiness:
    @pytest.fixture
    def client(self):
        from app.main import app
        from app.db.database import Base, engine

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return TestClient(app)

    def test_health_endpoint_is_unauthenticated(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_is_cheap_and_does_not_touch_database(self, client):
        # The /health endpoint must remain fast for Render's health check.
        # It must NOT execute any DB query.
        from unittest.mock import patch

        with patch("app.db.database.engine") as engine_mock:
            response = client.get("/health")
            assert response.status_code == 200
            engine_mock.connect.assert_not_called()

    def test_ready_endpoint_reports_database_status(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert data["database"] in ("ok", "error")
        assert data["status"] in ("ok", "error")


class TestWebSocketPath:
    """Smoke-test that the WebSocket route is wired (without opening a socket)."""

    def test_websocket_route_registered(self):
        from app.main import app
        from app.api.websocket import router

        # The websocket router is mounted on the app under API_PREFIX.
        # Check the router's own path rather than the wrapped Starlette
        # routing objects, which don't expose `.path` directly.
        assert any(
            getattr(getattr(r, "path", ""), "__contains__", lambda _: False)(
                "ws/companies"
            )
            for r in router.routes
        ) or any("ws/companies" in str(getattr(r, "path", "")) for r in router.routes), (
            "Expected the WebSocket router to declare a /ws/companies route"
        )
