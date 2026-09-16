"""Request ID middleware: correlation ID + per-request log context."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.context import bind_request_context, unbind_request_context

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        bind_request_context(request_id)
        try:
            response = await call_next(request)
        finally:
            unbind_request_context()
        response.headers[REQUEST_ID_HEADER] = request_id
        return response