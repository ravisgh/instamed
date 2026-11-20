"""Request id + access log middleware, and the catch-all error handler."""

import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import metrics
from app.core.config import Settings
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
            elapsed = time.perf_counter() - started
            elapsed_ms = elapsed * 1000
            metrics.observe(request, status_code, elapsed)
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


API_CSP = "default-src 'none'; frame-ancestors 'none'"
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Conservative browser security headers for a JSON API."""

    def __init__(self, app, hsts: bool):
        super().__init__(app)
        self.hsts = hsts

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "no-referrer")
        # Swagger UI pulls scripts and styles from a CDN, so it keeps the browser default.
        if not request.url.path.startswith(DOCS_PATHS):
            headers.setdefault("Content-Security-Policy", API_CSP)
        if self.hsts:
            headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def install(app: FastAPI, settings: Settings) -> None:
    # Added last = runs first: CORS answers preflights before anything else.
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    app.add_middleware(RequestContextMiddleware)
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
            expose_headers=[REQUEST_ID_HEADER],
            max_age=600,
        )
    app.add_exception_handler(Exception, unhandled_exception_handler)
