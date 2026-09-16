"""Structured JSON logging (structlog).

Every log event includes: timestamp, level, service, operation, and whatever
context we bind (request_id, user, latency, error...). Rendered as one JSON
line per event — grep/jq friendly, dashboard-ready.
"""

import logging
import sys

import structlog

from app.core.config import get_settings

# ============================================================
# Setup
# ============================================================

def setup_logging() -> None:
    """Configure stdlib + structlog. Called once at app startup."""
    settings = get_settings()

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger(name)