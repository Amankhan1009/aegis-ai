"""Integration tests for AI processing with a mocked provider."""

import pytest
from fastapi.testclient import TestClient

from app.providers.base import ChatMessage, LLMResult


class MockProvider:
    """Predictable provider replacing Groq in integration tests."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = 0

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        timeout_seconds: float = 30.0,
    ) -> LLMResult:
        self.calls += 1

        return LLMResult(
            content=self.content,
            input_tokens=12,
            output_tokens=8,
            latency_ms=15.5,
            model=model,
        )


def test_ai_process_returns_mocked_response(
    client: TestClient,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = MockProvider("Mocked AI response.")

    monkeypatch.setattr(
        "app.services.ai_service.get_provider",
        lambda: provider,
    )

    response = client.post(
        "/api/v1/ai/process",
        headers=admin_headers,
        json={
            "prompt": "Summarize the incident.",
            "temperature": 0.4,
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["output"] == "Mocked AI response."
    assert body["provider"] == "groq"
    assert body["model"] == "openai/gpt-oss-120b"
    assert body["input_tokens"] == 12
    assert body["output_tokens"] == 8
    assert body["latency_ms"] == 15.5
    assert body["validation_failed"] is False
    assert body["request_id"]
    assert provider.calls == 1


def test_ai_process_validates_structured_output(
    client: TestClient,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = MockProvider('{"summary": "Database latency is elevated.", "severity": "high"}')

    monkeypatch.setattr(
        "app.services.ai_service.get_provider",
        lambda: provider,
    )

    response = client.post(
        "/api/v1/ai/process",
        headers=admin_headers,
        json={
            "prompt": "Return the incident summary as JSON.",
            "structured_output": {
                "required_fields": ["summary", "severity"],
                "allowed_values": {
                    "severity": ["low", "medium", "high"],
                },
            },
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["structured_result"] == {
        "summary": "Database latency is elevated.",
        "severity": "high",
    }
    assert body["validation_failed"] is False
    assert provider.calls == 1


def test_invalid_output_returns_controlled_fallback(
    client: TestClient,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = MockProvider('{"summary": "unused"}')

    monkeypatch.setattr(
        "app.services.ai_service.get_provider",
        lambda: provider,
    )

    response = client.post(
        "/api/v1/ai/process",
        headers={
            **admin_headers,
            "X-Fail-Mode": "invalid",
        },
        json={
            "prompt": "Return a structured incident summary.",
            "structured_output": {
                "required_fields": ["summary"],
            },
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["validation_failed"] is True
    assert body["structured_result"] is None
    assert "temporarily unavailable or produced invalid output" in body["output"]
    assert provider.calls == 0


def test_ai_process_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/process",
        json={"prompt": "Unauthorized request."},
    )

    assert response.status_code == 401


def test_ai_process_rejects_empty_prompt(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/ai/process",
        headers=admin_headers,
        json={"prompt": ""},
    )

    assert response.status_code == 422

    body = response.json()
    assert body["error"] == "validation_error"
    assert body["message"] == "Request validation failed"
