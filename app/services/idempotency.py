"""Idempotency service backed by workflow_executions table.

Key lifecycle:
  1. INSERT row (status=started). If unique-violation → another request with the
     same key is in flight or done → fetch and return existing result.
  2. On success → update row (status=completed, result=...).
  3. On failure → update row (status=failed, error=...) so the client can retry.
"""

import json

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.workflow_execution import WorkflowExecution


def begin(db: Session, idempotency_key: str, request_id: str) -> WorkflowExecution | None:
    """Try to claim the key. Returns None if the key already exists (duplicate)."""
    row = WorkflowExecution(
        idempotency_key=idempotency_key,
        request_id=request_id,
        status="started",
    )
    db.add(row)
    try:
        db.commit()
        return row
    except IntegrityError:
        db.rollback()
        return None


def get_existing(db: Session, idempotency_key: str) -> WorkflowExecution:
    """Fetch the row for a duplicate request. Raises 409 if still in progress."""
    row = (
        db.query(WorkflowExecution)
        .filter(WorkflowExecution.idempotency_key == idempotency_key)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=500, detail="Idempotency state lost")
    if row.status == "started":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is still in progress",
        )
    return row


def complete(db: Session, row: WorkflowExecution, result: dict) -> None:
    row.status = "completed"
    row.result = result
    db.commit()


def fail(db: Session, row: WorkflowExecution, error: str) -> None:
    row.status = "failed"
    row.error = error
    db.commit()


def result_to_response(row: WorkflowExecution) -> dict:
    """Rebuild the API response from a stored completed row."""
    assert row.result is not None
    return json.loads(json.dumps(row.result))  # deep-copy as plain dict