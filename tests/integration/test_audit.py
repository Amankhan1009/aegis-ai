"""Integration tests for audit-event authorization."""

from fastapi.testclient import TestClient


def test_admin_can_list_audit_events(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/audit/events",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["count"] == 0
    assert body["events"] == []


def test_developer_cannot_list_audit_events(
    client: TestClient,
    developer_headers: dict[str, str],
) -> None:
    response = client.get(
        "/api/v1/audit/events",
        headers=developer_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"
