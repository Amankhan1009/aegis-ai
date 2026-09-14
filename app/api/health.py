"""System endpoints: liveness and readiness probes."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    """Liveness probe: the process is up."""
    return {"status": "ok", "service": get_settings().app_name}


@router.get("/ready")
def ready() -> dict:
    """Readiness probe.

    Real database (M4) and Redis (M9) checks are added later; for now this
    confirms the app can serve requests.
    """
    return {"status": "ready"}