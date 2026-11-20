from dataclasses import dataclass

from fastapi import Query


@dataclass
class Pagination:
    """Query params for list endpoints: `?skip=0&limit=20` (limit capped at 100)."""

    skip: int = Query(0, ge=0, description="Number of items to skip")
    limit: int = Query(20, ge=1, le=100, description="Max items to return (1-100)")
