"""Prometheus metrics. Labels use route *templates* (/orders/{order_id}), never raw paths,
so the number of time series stays small no matter how many ids are requested."""

import secrets

from fastapi import APIRouter, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "http_requests_total", "HTTP requests handled", ["method", "route", "status"]
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Time spent handling HTTP requests",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
ORDERS_PLACED = Counter("instamed_orders_placed_total", "Orders placed")
LOGIN_FAILURES = Counter("instamed_login_failures_total", "Failed login attempts")
RATE_LIMITED = Counter("instamed_rate_limited_total", "Requests rejected by rate limits", ["key"])


def route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


def observe(request: Request, status_code: int, seconds: float) -> None:
    route = route_template(request)
    if route == "/metrics":
        return
    HTTP_REQUESTS.labels(request.method, route, str(status_code)).inc()
    HTTP_LATENCY.labels(request.method, route).observe(seconds)


router = APIRouter(include_in_schema=False)


@router.get("/metrics")
async def metrics(request: Request) -> Response:
    token = request.app.state.settings.metrics_token
    if token:
        sent = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not secrets.compare_digest(sent, token.get_secret_value()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
