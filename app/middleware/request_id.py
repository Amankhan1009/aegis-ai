"""Request ID (correlation ID) middleware.

Generates a UUID per request (or honors an incoming X-Request-ID header so a
client retry can keep the same ID), stores it on request.state, and echoes it
back in the response. Logs, DB rows, and traces will reuse this same ID.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response