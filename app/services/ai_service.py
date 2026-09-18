"""AI orchestration service: reliability (M7) + metrics/cost (M11) + validation (M13)."""

# ==================== Imports ====================

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_usage import AIUsage
from app.models.failure import Failure
from app.observability import metrics
from app.observability.logging import get_logger
from app.observability.tracing import get_tracer
from app.providers.base import ChatMessage
from app.providers.factory import get_provider
from app.reliability.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.reliability.decorators import resilient_call
from app.schemas.ai import AIProcessRequest, AIProcessResponse
from app.services.failure_injection import FailingProvider, FailMode
from app.services.validation import (
    OutputValidationError,
    build_correction_prompt,
    validate_structured_output,
)

# ==================== Constants ====================

FALLBACK_MESSAGE = (
    "The AI model is temporarily unavailable or produced invalid output. "
    "Your request was received (request_id logged) — please retry shortly."
)


# ==================== Shared Reliability Components ====================

_llm_breaker = CircuitBreaker(
    name="llm",
    failure_threshold=3,
    recovery_timeout_seconds=20.0,
)

log = get_logger("ai.service")


# ==================== AI Request Processing ====================

def process_ai_request(
    payload: AIProcessRequest,
    db: Session,
    request: Request,
    fail_mode: str | None = None,
) -> AIProcessResponse:
    settings = get_settings()
    request_id = request.state.request_id

    # ==================== Build Messages ====================

    messages = [
        ChatMessage(
            role="user",
            content=payload.prompt,
        )
    ]

    if payload.system_prompt:
        messages.insert(
            0,
            ChatMessage(
                role="system",
                content=payload.system_prompt,
            ),
        )

    # ==================== Provider Setup ====================

    provider = get_provider()

    if fail_mode:
        provider = FailingProvider(
            provider,
            FailMode(fail_mode),
        )

    tracer = get_tracer()

    # ==================== M7: Reliable LLM Call ====================

    with tracer.start_as_current_span("ai.model_call") as span:
        span.set_attribute("llm.model", settings.ai_model)
        span.set_attribute("llm.provider", settings.ai_provider)

        try:
            result = resilient_call(
                lambda: provider.chat(
                    messages=messages,
                    model=settings.ai_model,
                    timeout_seconds=30.0,
                ),
                breaker=_llm_breaker,
                timeout_seconds=30.0,
                max_attempts=3,
            )

            span.set_attribute(
                "llm.input_tokens",
                result.input_tokens,
            )
            span.set_attribute(
                "llm.output_tokens",
                result.output_tokens,
            )
            span.set_attribute(
                "llm.latency_ms",
                result.latency_ms,
            )

        except CircuitOpenError as exc:
            span.set_attribute(
                "llm.outcome",
                "breaker_open",
            )

            metrics.LLM_REQUESTS.labels(
                provider=settings.ai_provider,
                model=settings.ai_model,
                outcome="breaker_open",
            ).inc()

            _record_failure(
                db,
                request_id,
                "ai.model_call",
                exc,
                retry_count=0,
            )

            return _fallback_response(
                settings,
                request_id,
            )

        except TimeoutError as exc:
            span.set_attribute(
                "llm.outcome",
                "timeout",
            )

            metrics.LLM_REQUESTS.labels(
                provider=settings.ai_provider,
                model=settings.ai_model,
                outcome="timeout",
            ).inc()

            _record_failure(
                db,
                request_id,
                "ai.model_call",
                exc,
                retry_count=3,
            )

            return _fallback_response(
                settings,
                request_id,
            )

        except Exception as exc:
            span.set_attribute(
                "llm.outcome",
                "error",
            )

            metrics.LLM_REQUESTS.labels(
                provider=settings.ai_provider,
                model=settings.ai_model,
                outcome="error",
            ).inc()

            _record_failure(
                db,
                request_id,
                "ai.model_call",
                exc,
                retry_count=3,
            )

            return _fallback_response(
                settings,
                request_id,
            )

        span.set_attribute(
            "llm.outcome",
            "success",
        )

    # ==================== M13: Structured Output Validation ====================

    structured_result: dict | None = None
    validation_failed = False

    if payload.structured_output is not None:
        spec = payload.structured_output

        try:
            structured_result = validate_structured_output(
                result.content,
                spec,
            )

        except OutputValidationError as exc:
            log.warning(
                "invalid_output",
                operation="ai.validation",
                error=str(exc),
                attempt=1,
            )

            metrics.LLM_INVALID_OUTPUT.inc()

            # One retry with a correction prompt
            retry_payload = payload.model_copy(
                update={
                    "prompt": build_correction_prompt(
                        payload.prompt,
                        spec,
                        str(exc),
                    )
                }
            )

            retry_messages = [
                ChatMessage(
                    role="user",
                    content=retry_payload.prompt,
                )
            ]

            if retry_payload.system_prompt:
                retry_messages.insert(
                    0,
                    ChatMessage(
                        role="system",
                        content=retry_payload.system_prompt,
                    ),
                )

            try:
                retry_result = resilient_call(
                    lambda: provider.chat(
                        messages=retry_messages,
                        model=settings.ai_model,
                        timeout_seconds=30.0,
                    ),
                    breaker=_llm_breaker,
                    timeout_seconds=30.0,
                    max_attempts=1,
                )

                result = retry_result

                structured_result = validate_structured_output(
                    result.content,
                    spec,
                )

                log.info(
                    "invalid_output_recovered",
                    operation="ai.validation",
                )

            except (OutputValidationError, Exception) as exc2:
                log.error(
                    "invalid_output_final",
                    operation="ai.validation",
                    error=str(exc2),
                )

                metrics.LLM_INVALID_OUTPUT.inc()
                validation_failed = True

                return _fallback_response(
                    settings,
                    request_id,
                    validation_failed=True,
                )

    # ==================== M11: Metrics and Cost Calculation ====================

    cost = metrics.estimate_cost_usd(
        result.model,
        result.input_tokens,
        result.output_tokens,
    )

    metrics.LLM_REQUESTS.labels(
        provider=settings.ai_provider,
        model=result.model,
        outcome="success",
    ).inc()

    metrics.LLM_TOKENS.labels(
        provider=settings.ai_provider,
        model=result.model,
        kind="input",
    ).inc(result.input_tokens)

    metrics.LLM_TOKENS.labels(
        provider=settings.ai_provider,
        model=result.model,
        kind="output",
    ).inc(result.output_tokens)

    metrics.LLM_LATENCY.labels(
        provider=settings.ai_provider,
        model=result.model,
    ).observe(result.latency_ms / 1000)

    metrics.ESTIMATED_COST_USD.labels(
        provider=settings.ai_provider,
        model=result.model,
    ).inc(cost)

    # ==================== Logging ====================

    log.info(
        "model_call_completed",
        operation="ai.model_call",
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        estimated_cost_usd=cost,
    )

    # ==================== Persist AI Usage ====================

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

    # ==================== Return Response ====================

    return AIProcessResponse(
        request_id=request_id,
        provider=settings.ai_provider,
        model=result.model,
        output=result.content,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        structured_result=structured_result,
        validation_failed=validation_failed,
    )


# ==================== Failure Persistence ====================

def _record_failure(
    db: Session,
    request_id: str,
    operation: str,
    exc: BaseException,
    retry_count: int = 0,
) -> None:
    """Persist a failure record (best-effort)."""

    try:
        db.add(
            Failure(
                request_id=request_id,
                operation=operation,
                error_type=type(exc).__name__,
                error_message=str(exc)[:500],
                retry_count=retry_count,
            )
        )

        db.commit()

    except Exception:
        db.rollback()


# ==================== Fallback Response ====================

def _fallback_response(
    settings,
    request_id: str,
    validation_failed: bool = False,
) -> AIProcessResponse:
    return AIProcessResponse(
        request_id=request_id,
        provider=settings.ai_provider,
        model=settings.ai_model,
        output=FALLBACK_MESSAGE,
        input_tokens=0,
        output_tokens=0,
        latency_ms=0.0,
        structured_result=None,
        validation_failed=validation_failed,
    )