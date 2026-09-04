"""Test-only environment setup for the application factory."""

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://revive:change-me-for-local-development@localhost:5432/revive"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_session_factory, get_engine, Base


@pytest.fixture(scope="session")
def engine():
    engine_obj = get_engine()
    Base.metadata.create_all(engine_obj)
    yield engine_obj
    Base.metadata.drop_all(engine_obj)


@pytest.fixture(scope="session", autouse=True)
def celery_config():
    from app.workers.celery_app import celery_app
    celery_app.conf.update(task_always_eager=True)


@pytest.fixture
def db_session(engine) -> Session:
    from app.core.database import get_session_factory
    # We should override the global session factory for tests to use the test engine, 
    # but since DATABASE_URL is set, get_session_factory() already uses it.
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    from app.core.database import get_db
    
    def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
