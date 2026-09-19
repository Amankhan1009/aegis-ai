"""Retry with exponential backoff + jitter.

Retryable = transient (network errors, 429, 5xx, timeouts).
Non-retryable = permanent (4xx validation, auth) — fail fast.
"""

import random
import time
from collections.abc import Callable
from typing import TypeVar

from app.observability.metrics import RETRY_COUNT

T = TypeVar("T")

RETRYABLE_EXCEPTIONS = (TimeoutError, ConnectionError)


class NonRetryableError(Exception):
    """Raise from a callable to fail immediately without retrying."""


def is_retryable(exc: BaseException) -> bool:
    """Classify an exception as retryable or not."""
    if isinstance(exc, NonRetryableError):
        return False
    # Groq SDK raises these for HTTP errors; duck-type to avoid importing it here
    status = getattr(exc, "status_code", None)
    if status is not None:
        return status == 429 or status >= 500
    return isinstance(exc, RETRYABLE_EXCEPTIONS)


def with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.5,
    max_delay_seconds: float = 8.0,
    sleep: Callable[[float], None] = time.sleep,
    operation: str = "unknown",
) -> T:
    """Run fn with retries. Returns fn's result or re-raises the last error."""
    last_exc: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc

            if attempt == max_attempts or not is_retryable(exc):
                raise

            RETRY_COUNT.labels(operation=operation).inc()

            delay = min(
                base_delay_seconds * (2 ** (attempt - 1)),
                max_delay_seconds,
            )

            sleep(delay + random.uniform(0, delay * 0.25))

    raise last_exc  # unreachable, satisfies type checkers
