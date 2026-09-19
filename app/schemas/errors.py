"""Shared API response schemas."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Consistent error body returned by every failed request."""

    error: str  # machine-readable code, e.g. "validation_error"
    message: str  # human-readable summary
    request_id: str  # correlation ID for tracing the failure
    detail: list[dict] | None = None
