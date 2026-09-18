"""AI processing endpoint (Milestones 6-12) with tracing."""

# ==================== Imports ====================

import time

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.observability import metrics
from app.observability.context import bind_request_context
from app.observability.logging import get_logger
from app.observability.tracing import get_tracer
from app.schemas.ai import AIProcessRequest, AIProcessResponse
from app.schemas.auth import CurrentUser
from app.services import audit, cache, idempotency, rate_limit
from app.services.ai_service import process_ai_request
from app.services.failure_injection import HEADER_NAME

# ==================== Router ====================

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["ai"],
)

log = get_logger("ai.endpoint")


# ==================== AI Processing Endpoint ====================

@router.post("/process", response_model=AIProcessResponse)
def process(
    payload: AIProcessRequest,
    request: Request,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
    fail_mode: str | None = Header(
        default=None,
        alias=HEADER_NAME,
    ),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> AIProcessResponse:
    start = time.perf_counter()

    bind_request_context(
        request.state.request_id,
        user.username,
    )

    log.info(
        "request_started",
        operation="ai.process",
        user=user.username,
    )

    tracer = get_tracer()

    with tracer.start_as_current_span("ai.process_endpoint") as span:
        span.set_attribute(
            "http.user",
            user.username,
        )

        span.set_attribute(
            "ai.idempotency_key",
            idempotency_key or "",
        )

        span.set_attribute(
            "ai.fail_mode",
            fail_mode or "",
        )

        # ==================== Rate Limiting ====================

        try:
            rate_limit.check_rate_limit(
                request,
                user.username,
            )

        except Exception:
            metrics.RATE_LIMIT_HITS.inc()

            metrics.REQUEST_COUNT.labels(
                endpoint="ai.process",
                status="429",
            ).inc()

            raise

        # ==================== Audit: Allowed Attempt ====================

        audit.record(
            db,
            actor=user.username,
            action="ai.process.attempt",
            outcome="allowed",
            request_id=request.state.request_id,
            metadata_={
                "idempotency_key": idempotency_key or "",
                "fail_mode": fail_mode or "",
            },
        )

        # ==================== Idempotency ====================

        claim = None

        if idempotency_key:
            claim = idempotency.begin(
                db,
                idempotency_key,
                request.state.request_id,
            )

            if claim is None:
                existing = idempotency.get_existing(
                    db,
                    idempotency_key,
                )

                log.info(
                    "idempotency_replay",
                    operation="ai.process",
                    idempotency_key=idempotency_key,
                )

                # Record idempotency replay
                audit.record(
                    db,
                    actor=user.username,
                    action="ai.process.replay",
                    outcome="success",
                    request_id=request.state.request_id,
                    metadata_={
                        "idempotency_key": idempotency_key or "",
                    },
                )

                return AIProcessResponse(
                    **idempotency.result_to_response(existing)
                )

        # ==================== Cache ====================

        cached = cache.get(payload)

        if cached is not None:
            metrics.CACHE_HITS.inc()

            if claim:
                idempotency.complete(
                    db,
                    claim,
                    cached.model_dump(),
                )

            log.info(
                "cache_hit",
                operation="ai.process",
            )

            # Record cache hit
            audit.record(
                db,
                actor=user.username,
                action="ai.process",
                outcome="success",
                request_id=request.state.request_id,
                metadata_={
                    "cached": True,
                    "fail_mode": fail_mode or "",
                },
            )

            return cached

        metrics.CACHE_MISSES.inc()

        log.info(
            "cache_miss",
            operation="ai.process",
        )

        # ==================== AI Processing ====================

        try:
            response = process_ai_request(
                payload,
                db,
                request,
                fail_mode=fail_mode,
            )

        except Exception as exc:
            if claim:
                idempotency.fail(
                    db,
                    claim,
                    str(exc),
                )

            log.error(
                "request_failed",
                operation="ai.process",
                error_type=type(exc).__name__,
                error=str(exc),
            )

            metrics.REQUEST_COUNT.labels(
                endpoint="ai.process",
                status="500",
            ).inc()

            # Record AI processing failure
            audit.record(
                db,
                actor=user.username,
                action="ai.process",
                outcome="failure",
                request_id=request.state.request_id,
                metadata_={
                    "error_type": type(exc).__name__,
                    "fail_mode": fail_mode or "",
                },
            )

            raise

        # ==================== Store Results ====================

        cache.set(
            payload,
            response,
        )

        if claim:
            idempotency.complete(
                db,
                claim,
                response.model_dump(),
            )

        # ==================== Metrics & Tracing ====================

        latency_ms = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        metrics.REQUEST_COUNT.labels(
            endpoint="ai.process",
            status="200",
        ).inc()

        metrics.REQUEST_LATENCY.labels(
            endpoint="ai.process",
        ).observe(latency_ms / 1000)

        span.set_attribute(
            "ai.input_tokens",
            response.input_tokens,
        )

        span.set_attribute(
            "ai.output_tokens",
            response.output_tokens,
        )

        # ==================== Structured Logging ====================

        log.info(
            "request_completed",
            operation="ai.process",
            status="success",
            latency_ms=latency_ms,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )

        # ==================== Audit ====================

        audit.record(
            db,
            actor=user.username,
            action="ai.process",
            outcome="success",
            request_id=request.state.request_id,
            metadata_={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cached": False,
                "validation_failed": response.validation_failed,
                "fail_mode": fail_mode or "",
            },
        )

        return response