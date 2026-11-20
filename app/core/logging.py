"""Logging setup: every log line carries the current request id."""

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"


class RequestIdFilter(logging.Filter):
    """Copy the request id from the context into each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line, for log shippers (Loki, ELK, CloudWatch...)."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def setup_logging(level: str = "INFO", fmt: str = "text") -> None:
    """Configure the `instamed` logger tree (safe to call again; last call wins)."""
    logger = logging.getLogger("instamed")
    logger.setLevel(level.upper())
    formatter = JsonFormatter() if fmt == "json" else logging.Formatter(LOG_FORMAT)
    if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
        handler = logging.StreamHandler()
        handler.addFilter(RequestIdFilter())
        logger.addHandler(handler)
        logger.addFilter(RequestIdFilter())
        logger.propagate = True  # let pytest's caplog and uvicorn see records too
    for handler in logger.handlers:
        handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"instamed.{name}")
