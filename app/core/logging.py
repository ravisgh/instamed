"""Logging setup: every log line carries the current request id."""

import logging
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"


class RequestIdFilter(logging.Filter):
    """Copy the request id from the context into each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(level: str = "INFO") -> None:
    """Configure the `instamed` logger tree once (safe to call again)."""
    logger = logging.getLogger("instamed")
    logger.setLevel(level.upper())
    if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handler.addFilter(RequestIdFilter())
        logger.addHandler(handler)
        logger.addFilter(RequestIdFilter())
        logger.propagate = True  # let pytest's caplog and uvicorn see records too


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"instamed.{name}")
