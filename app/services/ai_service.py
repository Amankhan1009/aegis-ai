"""AI orchestration service with reliability (M7) + metrics/cost (M11)."""

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_usage import AIUsage
from app.observability import metrics
from app.observability.logging import get_logger
from app.providers.base import ChatMessage
from app.providers.factory import get_provider
from app.reliability.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.reliability.decorators import resilient_call
from app.schemas.ai import AIProcessRequest, AIProcessResponse

FALLBACK_MESSAGE = (
    "The AI model is temporarily unavailable. Your request was received "
    "(request_id logged) — please retry shortly."
)

_llm_breaker = CircuitBreaker(name="llm", failure_threshold=3, recovery_timeout_seconds=20.0)
log = get_logger("ai.service")


def process_ai_request(
    payload: AIProcessRequest, db: Session, request: Request
) -> AIProcessResponse:
    settings = get_settings()
    request_id = request.state.request_id

    messages = [ChatMessage(role="user", content=payload.prompt)]
    if payload.system_prompt:
        messages.insert(0, ChatMessage(role="system", content=payload.system_prompt))

    provider = get_provider()

    try:
        result = resilient_call(
            lambda: provider.chat(messages=messages, model=settings.ai_model, timeout_seconds=30.0),
            breaker=_llm_breaker,
            timeout_seconds=30.0,
            max_attempts=3,
        )
    except CircuitOpenError:
        metrics.LLM_REQUESTS.labels(provider=settings.ai_provider, model=settings.ai_model, outcome="breaker_open").inc()
        return _fallback_response(settings, request_id)
    except TimeoutError:
        metrics.LLM_REQUESTS.labels(provider=settings.ai_provider, model=settings.ai_model, outcome="timeout").inc()
        return _fallback_response(settings, request_id)
    except Exception:
        metrics.LLM_REQUESTS.labels(provider=settings.ai_provider, model=settings.ai_model, outcome="error").inc()
        return _fallback_response(settings, request_id)

    cost = metrics.estimate_cost_usd(result.model, result.input_tokens, result.output_tokens)

    metrics.LLM_REQUESTS.labels(provider=settings.ai_provider, model=result.model, outcome="success").inc()
    metrics.LLM_TOKENS.labels(provider=settings.ai_provider, model=result.model, kind="input").inc(result.input_tokens)
    metrics.LLM_TOKENS.labels(provider=settings.ai_provider, model=result.model, kind="output").inc(result.output_tokens)
    metrics.LLM_LATENCY.labels(provider=settings.ai_provider, model=result.model).observe(result.latency_ms / 1000)
    metrics.ESTIMATED_COST_USD.labels(provider=settings.ai_provider, model=result.model).inc(cost)

    log.info(
        "model_call_completed",
        operation="ai.model_call",
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        estimated_cost_usd=cost,
    )

    usage = AIUsage(
        request_id=request_id,
        provider=settings.ai_provider,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        estimated_cost_usd=cost,
    )
    db.add(usage)
    db.commit()

    return AIProcessResponse(
        request_id=request_id,
        provider=settings.ai_provider,
        model=result.model,
        output=result.content,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
    )


def _fallback_response(settings, request_id: str) -> AIProcessResponse:
    return AIProcessResponse(
        request_id=request_id,
        provider=settings.ai_provider,
        model=settings.ai_model,
        output=FALLBACK_MESSAGE,
        input_tokens=0,
        output_tokens=0,
        latency_ms=0.0,
    )