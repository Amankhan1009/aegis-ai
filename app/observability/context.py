"""Per-request log context helpers.

Binds request_id/user into structlog contextvars so every log line emitted
during a request automatically carries them — no passing loggers around.
"""

import structlog


def bind_request_context(request_id: str, user: str | None = None) -> None:
    structlog.contextvars.bind_contextvars(request_id=request_id, user=user or "anonymous")


def unbind_request_context() -> None:
    structlog.contextvars.unbind_contextvars("request_id", "user")
