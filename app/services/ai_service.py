"""AI orchestration service with reliability wrapping (Milestone 7).

Flow: breaker → retry/backoff → provider call (timeout inside provider).
On CircuitOpenError we return a controlled fallback instead of crashing.
"""

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_usage import AIUsage
from app.providers.base import ChatMessage
from app.providers.factory import get_provider
from app.reliability.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.reliability.decorators import resilient_call
from app.schemas.ai import AIProcessRequest, AIProcessResponse

FALLBACK_MESSAGE = (
    "The AI model is temporarily unavailable. Your request was received "
    "(request_id logged) — please retry shortly."
)

# One breaker per process; in production this lives in app state (Milestone 11
# will expose trip counts as metrics).
_llm_breaker = CircuitBreaker(name="llm", failure_threshold=3, recovery_timeout_seconds=20.0)


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
        return _fallback_response(settings, request_id, reason="circuit_open")
    except TimeoutError:
        return _fallback_response(settings, request_id, reason="timeout_after_retries")
    except Exception:
        return _fallback_response(settings, request_id, reason="provider_error")

    usage = AIUsage(
        request_id=request_id,
        provider=settings.ai_provider,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        estimated_cost_usd=0.0,
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


def _fallback_response(settings, request_id: str, reason: str) -> AIProcessResponse:
    """Controlled degradation — never crash the caller."""
    return AIProcessResponse(
        request_id=request_id,
        provider=settings.ai_provider,
        model=settings.ai_model,
        output=FALLBACK_MESSAGE,
        input_tokens=0,
        output_tokens=0,
        latency_ms=0.0,
    )