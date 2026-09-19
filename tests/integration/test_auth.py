"""Integration tests for JWT authentication."""

from fastapi.testclient import TestClient


def test_login_returns_bearer_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin-pass-123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_invalid_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
