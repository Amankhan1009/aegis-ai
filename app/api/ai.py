"""AI processing endpoint (Milestone 6).

Reliability wrapping (timeout/retry/breaker/fallback), rate limiting, caching,
and idempotency are layered on in Milestones 7-9.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.schemas.ai import AIProcessRequest, AIProcessResponse
from app.schemas.auth import CurrentUser
from app.services.ai_service import process_ai_request

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/process", response_model=AIProcessResponse)
def process(
    payload: AIProcessRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> AIProcessResponse:
    return process_ai_request(payload, db, request)