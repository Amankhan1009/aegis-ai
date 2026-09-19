"""FastAPI application entrypoint."""

from fastapi import FastAPI, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.ai import router as ai_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.protected import router as protected_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.observability.logging import setup_logging
from app.observability.metrics import metrics_response
from app.observability.tracing import setup_tracing

# ============================================================
# App factory
# ============================================================


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()
    setup_tracing()

    app = FastAPI(title=settings.app_name, version="0.12.0")

    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(protected_router)
    app.include_router(ai_router)
    app.include_router(audit_router)

    @app.get("/metrics")
    def metrics() -> Response:
        payload, content_type = metrics_response()
        return Response(content=payload, media_type=content_type)

    # Auto-traces incoming HTTP requests (creates the parent span).
    FastAPIInstrumentor.instrument_app(app)
    return app


app = create_app()
