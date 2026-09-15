"""Database engine and session management.

Connection string comes from Settings.database_url (env var). Business code
never touches the engine directly — it uses the session dependency.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# ============================================================
# Session dependency (FastAPI)
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """Yield a database session and guarantee it closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()