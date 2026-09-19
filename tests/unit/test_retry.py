"""Unit tests for retry classification and exponential backoff."""

import pytest

from app.reliability.retry import (
    NonRetryableError,
    is_retryable,
    with_retry,
)


class HTTPStatusError(Exception):
    """Small error type with the provider-compatible status_code attribute."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}")


def test_retryable_error_classification() -> None:
    assert is_retryable(TimeoutError("timeout"))
    assert is_retryable(ConnectionError("connection failed"))
    assert is_retryable(HTTPStatusError(429))
    assert is_retryable(HTTPStatusError(500))
    assert is_retryable(HTTPStatusError(503))


def test_non_retryable_error_classification() -> None:
    assert not is_retryable(NonRetryableError("invalid request"))
    assert not is_retryable(HTTPStatusError(400))
    assert not is_retryable(HTTPStatusError(401))
    assert not is_retryable(ValueError("invalid input"))


def test_retry_returns_successful_result_after_transient_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "app.reliability.retry.random.uniform",
        lambda _start, _end: 0.0,
    )

    def eventually_succeeds() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError("temporary timeout")
        return "success"

    result = with_retry(
        eventually_succeeds,
        max_attempts=3,
        base_delay_seconds=0.5,
        sleep=sleeps.append,
    )

    assert result == "success"
    assert attempts == 3
    assert sleeps == [0.5, 1.0]


def test_non_retryable_error_fails_without_retry() -> None:
    attempts = 0

    def always_fails() -> None:
        nonlocal attempts
        attempts += 1
        raise NonRetryableError("bad request")

    with pytest.raises(NonRetryableError, match="bad request"):
        with_retry(always_fails, max_attempts=3)

    assert attempts == 1


def test_retry_reraises_error_after_max_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0
    sleeps: list[float] = []

    monkeypatch.setattr(
        "app.reliability.retry.random.uniform",
        lambda _start, _end: 0.0,
    )

    def always_fails() -> None:
        nonlocal attempts
        attempts += 1
        raise ConnectionError("provider unavailable")

    with pytest.raises(ConnectionError, match="provider unavailable"):
        with_retry(
            always_fails,
            max_attempts=3,
            base_delay_seconds=0.5,
            sleep=sleeps.append,
        )

    assert attempts == 3
    assert sleeps == [0.5, 1.0]


def test_retry_delay_is_capped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    monkeypatch.setattr(
        "app.reliability.retry.random.uniform",
        lambda _start, _end: 0.0,
    )

    with pytest.raises(TimeoutError):
        with_retry(
            lambda: (_ for _ in ()).throw(TimeoutError("timeout")),
            max_attempts=4,
            base_delay_seconds=1.0,
            max_delay_seconds=2.0,
            sleep=sleeps.append,
        )

    assert sleeps == [1.0, 2.0, 2.0]
