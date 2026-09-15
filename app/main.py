"""FastAPI application entrypoint.

Run locally with: uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.protected import router as protected_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.middleware.request_id import RequestIDMiddleware

# ============================================================
# App factory
# ============================================================

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.5.0")

    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(protected_router)
    app.include_router(ai_router)
    return app


app = create_app()