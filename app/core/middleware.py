"""Request id + access log middleware, and the catch-all error handler."""

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger, request_id_var

REQUEST_ID_HEADER = "X-Request-ID"

access_log = get_logger("access")
error_log = get_logger("errors")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Give every request an id (or keep the caller's), log it, and echo it back."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id  # survives for the outer error handler
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            access_log.info(
                "%s %s %s %.1fms", request.method, request.url.path, status_code, elapsed_ms
            )
            request_id_var.reset(token)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log the real error, but never leak internals to the client."""
    request_id = getattr(request.state, "request_id", None) or request_id_var.get()
    token = request_id_var.set(request_id)
    try:
        error_log.exception("Unhandled error on %s %s", request.method, request.url.path)
    finally:
        request_id_var.reset(token)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
        headers={REQUEST_ID_HEADER: request_id},
    )


def install(app: FastAPI) -> None:
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)
