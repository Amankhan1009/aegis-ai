"""Unit tests for resilient-call composition."""

import httpx
import pytest

from app.reliability.circuit_breaker import (
    BreakerState,
    CircuitBreaker,
    CircuitOpenError,
)
from app.reliability.decorators import resilient_call


def test_resilient_call_returns_successful_result() -> None:
    breaker = CircuitBreaker(name="llm")

    result = resilient_call(
        lambda: "AI response",
        breaker=breaker,
        max_attempts=1,
    )

    assert result == "AI response"
    assert breaker.state == BreakerState.CLOSED


def test_resilient_call_converts_httpx_timeout_to_timeout_error() -> None:
    breaker = CircuitBreaker(name="llm", failure_threshold=2)

    def times_out() -> None:
        raise httpx.ReadTimeout("provider timeout")

    with pytest.raises(TimeoutError, match="provider timeout"):
        resilient_call(
            times_out,
            breaker=breaker,
            max_attempts=1,
        )

    assert breaker.state == BreakerState.CLOSED


def test_resilient_call_respects_open_circuit() -> None:
    breaker = CircuitBreaker(name="llm", failure_threshold=1)

    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("provider unavailable")))

    called = False

    def should_not_run() -> str:
        nonlocal called
        called = True
        return "unexpected"

    with pytest.raises(CircuitOpenError, match="Circuit 'llm' is OPEN"):
        resilient_call(
            should_not_run,
            breaker=breaker,
            max_attempts=1,
        )

    assert called is False
