"""Sliding-window rate limiting for sensitive endpoints (login, register).

The counters live in this process's memory. That is enough for a single API process; with
several workers or replicas each keeps its own counters, so put a shared store (e.g. Redis)
behind `RateLimiter` before scaling out.
"""

import math
import time
from collections import deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.core.logging import get_logger
from app.core.metrics import RATE_LIMITED

log = get_logger("ratelimit")


class RateLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}

    def hit(self, key: str, limit: int, window: float) -> int | None:
        """Record one attempt. Returns None if allowed, else seconds to wait."""
        now = self._clock()
        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= now - window:
            hits.popleft()
        if len(hits) >= limit:
            return max(1, math.ceil(hits[0] + window - now))
        hits.append(now)
        return None

    def reset(self) -> None:
        self._hits.clear()


def client_ip(request: Request) -> str:
    # Behind a proxy, run uvicorn with --proxy-headers so this is the real client address.
    return request.client.host if request.client else "unknown"


def enforce(request: Request, key: str, limit: int, window: float) -> None:
    """429 with Retry-After when `key` has used up its `limit` within `window` seconds."""
    settings = request.app.state.settings
    if not settings.rate_limit_enabled:
        return
    retry_after = request.app.state.rate_limiter.hit(key, limit, window)
    if retry_after is not None:
        kind = key.split(":", 1)[0]
        log.warning("Rate limit hit for %s", kind)
        RATE_LIMITED.labels(kind).inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts, try again later",
            headers={"Retry-After": str(retry_after)},
        )
