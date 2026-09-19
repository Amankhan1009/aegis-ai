"""Groq provider — talks to the Groq API via the official SDK (httpx under the hood)."""

import time

from groq import Groq

from app.core.config import get_settings
from app.providers.base import ChatMessage, LLMResult, ModelProvider


class GroqProvider(ModelProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set (see .env)")
        self._client = Groq(api_key=settings.groq_api_key)

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        timeout_seconds: float = 30.0,
    ) -> LLMResult:
        start = time.perf_counter()
        response = self._client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            timeout=timeout_seconds,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        usage = response.usage
        return LLMResult(
            content=response.choices[0].message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_ms=round(latency_ms, 2),
            model=model,
            raw=response.model_dump(),
        )
