"""AI processing endpoint (Milestones 6-11) with metrics emission."""

import time

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.observability import metrics
from app.observability.context import bind_request_context
from app.observability.logging import get_logger
from app.schemas.ai import AIProcessRequest, AIProcessResponse
from app.schemas.auth import CurrentUser
from app.services import cache, idempotency, rate_limit
from app.services.ai_service import process_ai_request

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
log = get_logger("ai.endpoint")


@router.post("/process", response_model=AIProcessResponse)
def process(
    payload: AIProcessRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> AIProcessResponse:
    start = time.perf_counter()
    bind_request_context(request.state.request_id, user.username)
    log.info("request_started", operation="ai.process", user=user.username)

    try:
        rate_limit.check_rate_limit(request, user.username)
    except Exception:
        metrics.RATE_LIMIT_HITS.inc()
        metrics.REQUEST_COUNT.labels(endpoint="ai.process", status="429").inc()
        raise

    claim = None
    if idempotency_key:
        claim = idempotency.begin(db, idempotency_key, request.state.request_id)
        if claim is None:
            existing = idempotency.get_existing(db, idempotency_key)
            log.info("idempotency_replay", operation="ai.process", idempotency_key=idempotency_key)
            return AIProcessResponse(**idempotency.result_to_response(existing))

    cached = cache.get(payload)
    if cached is not None:
        metrics.CACHE_HITS.inc()
        if claim:
            idempotency.complete(db, claim, cached.model_dump())
        log.info("cache_hit", operation="ai.process")
        return cached
    metrics.CACHE_MISSES.inc()
    log.info("cache_miss", operation="ai.process")

    try:
        response = process_ai_request(payload, db, request)
    except Exception as exc:
        if claim:
            idempotency.fail(db, claim, str(exc))
        log.error("request_failed", operation="ai.process", error_type=type(exc).__name__, error=str(exc))
        metrics.REQUEST_COUNT.labels(endpoint="ai.process", status="500").inc()
        raise

    cache.set(payload, response)
    if claim:
        idempotency.complete(db, claim, response.model_dump())

    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    metrics.REQUEST_COUNT.labels(endpoint="ai.process", status="200").inc()
    metrics.REQUEST_LATENCY.labels(endpoint="ai.process").observe(latency_ms / 1000)
    log.info(
        "request_completed",
        operation="ai.process",
        status="success",
        latency_ms=latency_ms,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )
    return response