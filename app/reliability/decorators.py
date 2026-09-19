"""Compose timeout + retry + circuit breaker around a callable."""

from collections.abc import Callable
from typing import TypeVar

import httpx

from app.reliability.circuit_breaker import CircuitBreaker
from app.reliability.retry import with_retry

T = TypeVar("T")


def resilient_call(
    fn: Callable[[], T],
    *,
    breaker: CircuitBreaker,
    timeout_seconds: float = 30.0,
    max_attempts: int = 3,
) -> T:
    """Run fn with: circuit breaker → retry/backoff → timeout on each attempt."""

    def attempt() -> T:
        try:
            return fn()
        except httpx.TimeoutException as exc:
            raise TimeoutError(str(exc)) from exc

    return breaker.call(lambda: with_retry(attempt, max_attempts=max_attempts))
