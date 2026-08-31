import os

# Configure a local SQLite database BEFORE importing the application so that
# the engine/session are bound to SQLite (no PostgreSQL required for tests).
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_agent_company.db")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.database import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def _reset_db():
    # Dispose all connections in the pool before dropping tables.
    # This prevents SQLite database locking when connections are still open.
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_suite_sanity():
    # Ensures the engine is bound to a SQLite URL in tests.
    assert engine.url.drivername == "sqlite"
