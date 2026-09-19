"""Global exception handlers — one consistent error shape for the whole API."""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.errors import ErrorResponse


class AppError(Exception):
    """Base class for expected application errors (raised by services later)."""

    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        body = ErrorResponse(error=exc.code, message=exc.message, request_id=_request_id(request))
        return JSONResponse(status_code=exc.http_status, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        body = ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            request_id=_request_id(request),
            detail=jsonable_encoder(exc.errors()),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=body.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        body = ErrorResponse(
            error="internal_error",
            message="Unexpected server error",
            request_id=_request_id(request),
        )
        return JSONResponse(status_code=500, content=body.model_dump())
