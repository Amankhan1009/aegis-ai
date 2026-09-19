"""Shared pytest fixtures using an isolated PostgreSQL test container."""

import os
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope="session")
def test_application() -> Generator[dict[str, Any], None, None]:
    """Start an isolated PostgreSQL database and create the test schema."""
    with PostgresContainer(
        "postgres:16-alpine",
        username="test_user",
        password="test_password",
        dbname="ai_ops_test",
    ) as postgres:
        database_url = postgres.get_connection_url().replace(
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
        )

        # Must be set before application modules read Settings.
        os.environ["DATABASE_URL"] = database_url
        os.environ["REDIS_URL"] = "redis://localhost:6379/15"
        os.environ["JWT_SECRET_KEY"] = "test-only-jwt-secret-key-at-least-32-chars"
        os.environ["GROQ_API_KEY"] = "test-groq-key-not-used"
        os.environ["APP_ENV"] = "test"

        from app.core.config import get_settings

        get_settings.cache_clear()

        from app.core.database import Base, SessionLocal, engine, get_db
        from app.main import app
        from app.models.ai_usage import AIUsage
        from app.models.audit_event import AuditEvent
        from app.models.failure import Failure
        from app.models.request_log import RequestLog
        from app.models.workflow_execution import WorkflowExecution

        # Model imports register all table definitions with Base.metadata.
        _ = (AIUsage, AuditEvent, Failure, RequestLog, WorkflowExecution)

        Base.metadata.create_all(bind=engine)

        yield {
            "app": app,
            "base": Base,
            "engine": engine,
            "get_db": get_db,
            "session_local": SessionLocal,
        }

        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def clean_database(test_application: dict[str, Any]) -> Generator[None, None, None]:
    """Clear test data before every test."""
    base = test_application["base"]
    engine = test_application["engine"]

    with engine.begin() as connection:
        for table in reversed(base.metadata.sorted_tables):
            connection.execute(table.delete())

    yield


@pytest.fixture
def client(
    test_application: dict[str, Any],
    clean_database: None,
) -> Generator[TestClient, None, None]:
    """FastAPI test client wired to the isolated PostgreSQL database."""
    app = test_application["app"]
    get_db = test_application["get_db"]
    session_local = test_application["session_local"]

    def override_get_db() -> Generator[Any, None, None]:
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    """JWT authorization headers for the seeded admin user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin-pass-123"},
    )
    assert response.status_code == 200

    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def developer_headers(client: TestClient) -> dict[str, str]:
    """JWT authorization headers for the seeded developer user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "dev", "password": "dev-pass-123"},
    )
    assert response.status_code == 200

    return {"Authorization": f"Bearer {response.json()['access_token']}"}
