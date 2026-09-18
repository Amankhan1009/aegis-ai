"""Audit trail service.

Writes one audit_events row per important action. Reads are ADMIN-only
(enforced at the API layer). Never log secrets or full prompts — metadata
is limited to safe operational fields.
"""

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.observability.logging import get_logger

log = get_logger("audit")


def record(
    db: Session,
    *,
    actor: str,
    action: str,
    outcome: str,
    request_id: str | None = None,
    resource: str | None = None,
    metadata_: dict | None = None,
) -> None:
    """Persist an audit event. Failures are logged, never raised (audit must
    not break the business flow)."""
    try:
        db.add(
            AuditEvent(
                request_id=request_id,
                actor=actor,
                action=action,
                resource=resource,
                outcome=outcome,
                metadata_=metadata_ or {},
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        log.error("audit_write_failed", operation="audit.record", error=str(exc))