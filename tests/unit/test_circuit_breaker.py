"""Unit tests for circuit-breaker state transitions."""

import pytest

from app.reliability.circuit_breaker import (
    BreakerState,
    CircuitBreaker,
    CircuitOpenError,
)


def test_successful_call_keeps_breaker_closed() -> None:
    breaker = CircuitBreaker(name="llm")

    result = breaker.call(lambda: "success")

    assert result == "success"
    assert breaker.state == BreakerState.CLOSED
    assert breaker.trip_count == 0


def test_breaker_opens_after_failure_threshold() -> None:
    breaker = CircuitBreaker(name="llm", failure_threshold=2)

    def fail() -> None:
        raise ConnectionError("provider unavailable")

    with pytest.raises(ConnectionError):
        breaker.call(fail)

    assert breaker.state == BreakerState.CLOSED

    with pytest.raises(ConnectionError):
        breaker.call(fail)

    assert breaker.state == BreakerState.OPEN
    assert breaker.trip_count == 1


def test_open_breaker_fails_fast_without_calling_function() -> None:
    breaker = CircuitBreaker(name="llm", failure_threshold=1)

    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("failure")))

    called = False

    def should_not_run() -> str:
        nonlocal called
        called = True
        return "unexpected"

    with pytest.raises(CircuitOpenError, match="Circuit 'llm' is OPEN"):
        breaker.call(should_not_run)

    assert called is False


def test_breaker_moves_to_half_open_after_recovery_timeout() -> None:
    now = [100.0]
    breaker = CircuitBreaker(
        name="llm",
        failure_threshold=1,
        recovery_timeout_seconds=10.0,
        clock=lambda: now[0],
    )

    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("failure")))

    assert breaker.state == BreakerState.OPEN

    now[0] = 110.0

    assert breaker.state == BreakerState.HALF_OPEN


def test_successful_half_open_call_closes_breaker() -> None:
    now = [100.0]
    breaker = CircuitBreaker(
        name="llm",
        failure_threshold=1,
        recovery_timeout_seconds=10.0,
        clock=lambda: now[0],
    )

    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("failure")))

    now[0] = 110.0

    assert breaker.call(lambda: "recovered") == "recovered"
    assert breaker.state == BreakerState.CLOSED
    assert breaker.trip_count == 1


def test_failed_half_open_call_reopens_breaker() -> None:
    now = [100.0]
    breaker = CircuitBreaker(
        name="llm",
        failure_threshold=1,
        recovery_timeout_seconds=10.0,
        clock=lambda: now[0],
    )

    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("failure")))

    now[0] = 110.0

    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("still failing")))

    assert breaker.state == BreakerState.OPEN
    assert breaker.trip_count == 2
