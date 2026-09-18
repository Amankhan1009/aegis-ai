"""Controlled failure simulation.

Activated ONLY via the X-Fail-Mode header (set by tests/demo scripts, never
by normal clients). Modes:
  - timeout   : provider sleeps past the timeout
  - error_500 : provider raises a fake 500
  - rate_limit: provider raises a fake 429
  - invalid   : provider returns malformed output (bypasses real model)
  - db_timeout: the DB session is forced to fail on commit

This is how we demonstrate Failure → Detection → Retry → Fallback → Logging →
Metrics → Dashboard (Milestone 20) without touching the real Groq API.
"""

from enum import StrEnum

from app.providers.base import ChatMessage, LLMResult


class FailMode(StrEnum):
    TIMEOUT = "timeout"
    ERROR_500 = "error_500"
    RATE_LIMIT = "rate_limit"
    INVALID = "invalid"
    DB_TIMEOUT = "db_timeout"


HEADER_NAME = "X-Fail-Mode"


class FakeHTTPError(Exception):
    """Mimics the Groq SDK's HTTP error shape (has status_code)."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


class FailingProvider:
    """Wraps the real provider and injects faults based on mode."""

    def __init__(self, real_provider, mode: FailMode) -> None:
        self._real = real_provider
        self._mode = mode

    def chat(self, messages: list[ChatMessage], model: str, timeout_seconds: float = 30.0) -> LLMResult:
        if self._mode == FailMode.TIMEOUT:
            import time

            time.sleep(timeout_seconds + 1)  # guarantees a timeout
            raise AssertionError("unreachable: sleep should have timed out")
        if self._mode == FailMode.ERROR_500:
            raise FakeHTTPError(500, "injected internal server error")
        if self._mode == FailMode.RATE_LIMIT:
            raise FakeHTTPError(429, "injected rate limit")
        if self._mode == FailMode.INVALID:
            return LLMResult(
                content="this is not json at all {{{",
                input_tokens=10,
                output_tokens=8,
                latency_ms=5.0,
                model=model,
            )
        return self._real.chat(messages, model, timeout_seconds)