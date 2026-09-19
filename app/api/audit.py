"""Audit log queries — ADMIN only (least privilege)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_roles
from app.core.database import get_db
from app.models.audit_event import AuditEvent
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/events")
def list_events(
    limit: int = 50,
    actor: str | None = None,
    outcome: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict:
    """Recent audit events, newest first. Filters optional."""
    q = db.query(AuditEvent)
    if actor:
        q = q.filter(AuditEvent.actor == actor)
    if outcome:
        q = q.filter(AuditEvent.outcome == outcome)
    rows = q.order_by(AuditEvent.created_at.desc()).limit(min(limit, 200)).all()
    return {
        "count": len(rows),
        "events": [
            {
                "id": str(r.id),
                "request_id": r.request_id,
                "actor": r.actor,
                "action": r.action,
                "resource": r.resource,
                "outcome": r.outcome,
                "metadata": r.metadata_,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }
