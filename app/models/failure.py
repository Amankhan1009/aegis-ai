"""Recorded failures (timeouts, retries exhausted, breaker trips, etc.)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Failure(Base):
    __tablename__ = "failures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    operation: Mapped[str] = mapped_column(String(128))
    error_type: Mapped[str] = mapped_column(String(128))
    error_message: Mapped[str] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)