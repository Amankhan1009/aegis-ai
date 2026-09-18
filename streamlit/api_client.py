"""HTTP client for the AegisAI FastAPI backend."""

import os
from typing import Any

import requests

# ============================================================
# Configuration
# ============================================================

API_URL = os.getenv("STREAMLIT_API_URL", "http://localhost:8000").rstrip("/")


# ============================================================
# Error handling
# ============================================================


class APIClientError(Exception):
    """A backend or network error safe to present in the dashboard."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


def _response_error(response: requests.Response) -> APIClientError:
    """Build a useful error from the API's standard error payload."""
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    detail = payload.get("detail") or payload.get("message") or response.reason
    return APIClientError(str(detail), response.status_code)


def _request(method: str, path: str, **kwargs: Any) -> requests.Response:
    """Send one request and normalize transport and HTTP errors."""
    try:
        response = requests.request(method, f"{API_URL}{path}", **kwargs)
    except requests.Timeout as exc:
        raise APIClientError("The API request timed out. Please try again.") from exc
    except requests.ConnectionError as exc:
        raise APIClientError(
            f"Cannot connect to the API at {API_URL}. Confirm the backend is running."
        ) from exc
    except requests.RequestException as exc:
        raise APIClientError(f"API request failed: {exc}") from exc
    if not response.ok:
        raise _response_error(response)
    return response


# ============================================================
# Authentication
# ============================================================


def login(username: str, password: str) -> dict:
    """Authenticate against the FastAPI backend."""
    return _request(
        "POST",
        "/api/v1/auth/login",
        data={"username": username, "password": password},
        timeout=10,
    ).json()


# ============================================================
# Health
# ============================================================


def health() -> dict:
    """Get API liveness status."""
    return _request("GET", "/health", timeout=10).json()


def ready() -> dict:
    """Get API readiness status."""
    return _request("GET", "/ready", timeout=10).json()


# ============================================================
# AI
# ============================================================


def process_ai(
    token: str,
    payload: dict,
    fail_mode: str | None = None,
) -> dict:
    """Send an authenticated AI processing request."""
    headers = {"Authorization": f"Bearer {token}"}

    if fail_mode:
        headers["X-Fail-Mode"] = fail_mode

    return _request(
        "POST",
        "/api/v1/ai/process",
        json=payload,
        headers=headers,
        timeout=95,
    ).json()


# ============================================================
# Audit
# ============================================================


def get_audit_events(
    token: str,
    limit: int = 50,
    actor: str | None = None,
    outcome: str | None = None,
) -> dict:
    """Get audit events from the backend."""
    headers = {"Authorization": f"Bearer {token}"}

    params: dict[str, str | int] = {"limit": limit}

    if actor:
        params["actor"] = actor

    if outcome:
        params["outcome"] = outcome

    return _request(
        "GET",
        "/api/v1/audit/events",
        headers=headers,
        params=params,
        timeout=10,
    ).json()


# ============================================================
# Metrics
# ============================================================


def get_metrics() -> str:
    """Get the raw Prometheus metrics payload."""
    return _request("GET", "/metrics", timeout=10).text
