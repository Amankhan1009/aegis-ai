"""FastAPI application entrypoint.

Run locally with: uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.middleware.request_id import RequestIDMiddleware


# ============================================================
# App factory
# ============================================================

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.3.0")

    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    return app


app = create_app()