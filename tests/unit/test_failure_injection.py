"""Unit tests for controlled AI provider failure injection."""

import pytest

from app.providers.base import ChatMessage, LLMResult
from app.services.failure_injection import FailingProvider, FailMode, FakeHTTPError


class StubProvider:
    """Predictable provider used to verify the failure wrapper."""

    def __init__(self) -> None:
        self.calls = 0
        self.result = LLMResult(
            content='{"summary": "normal provider response"}',
            input_tokens=11,
            output_tokens=7,
            latency_ms=12.5,
            model="test-model",
        )

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        timeout_seconds: float = 30.0,
    ) -> LLMResult:
        self.calls += 1
        return self.result


def test_normal_mode_delegates_to_real_provider() -> None:
    provider = StubProvider()
    failing_provider = FailingProvider(provider, FailMode.DB_TIMEOUT)

    result = failing_provider.chat(
        messages=[ChatMessage(role="user", content="Hello")],
        model="test-model",
    )

    assert result == provider.result
    assert provider.calls == 1


def test_invalid_mode_returns_malformed_output() -> None:
    provider = StubProvider()
    failing_provider = FailingProvider(provider, FailMode.INVALID)

    result = failing_provider.chat(
        messages=[ChatMessage(role="user", content="Hello")],
        model="test-model",
    )

    assert result.content == "this is not json at all {{{"
    assert result.input_tokens == 10
    assert result.output_tokens == 8
    assert provider.calls == 0


def test_error_500_mode_raises_fake_http_error() -> None:
    provider = StubProvider()
    failing_provider = FailingProvider(provider, FailMode.ERROR_500)

    with pytest.raises(FakeHTTPError) as exc_info:
        failing_provider.chat(
            messages=[ChatMessage(role="user", content="Hello")],
            model="test-model",
        )

    assert exc_info.value.status_code == 500
    assert provider.calls == 0


def test_rate_limit_mode_raises_fake_http_error() -> None:
    provider = StubProvider()
    failing_provider = FailingProvider(provider, FailMode.RATE_LIMIT)

    with pytest.raises(FakeHTTPError) as exc_info:
        failing_provider.chat(
            messages=[ChatMessage(role="user", content="Hello")],
            model="test-model",
        )

    assert exc_info.value.status_code == 429
    assert provider.calls == 0


def test_timeout_mode_sleeps_past_timeout_without_waiting(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = StubProvider()
    failing_provider = FailingProvider(provider, FailMode.TIMEOUT)
    slept_for: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept_for.append(seconds)

    monkeypatch.setattr("time.sleep", fake_sleep)

    with pytest.raises(AssertionError, match="unreachable"):
        failing_provider.chat(
            messages=[ChatMessage(role="user", content="Hello")],
            model="test-model",
            timeout_seconds=2.0,
        )

    assert slept_for == [3.0]
    assert provider.calls == 0
