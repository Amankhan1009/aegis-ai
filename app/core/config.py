"""Application configuration.

All settings are loaded from environment variables and/or the local .env file
via pydantic-settings. Secrets are NEVER hardcoded here — this module only
declares names, types, and safe defaults.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# ============================================================
# Settings
# ============================================================

class Settings(BaseSettings):
    """Runtime configuration for the platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # tolerate unrelated env vars
    )

    # --- Core ---
    app_env: str = "local"
    app_name: str = "enterprise-ai-ops"
    api_port: int = 8000
    log_level: str = "INFO"

    # --- AI provider (see docs/AI_MODEL_STRATEGY.md) ---
    ai_provider: str = "groq"
    ai_model: str = "openai/gpt-oss-120b"
    groq_api_key: str = ""

    # --- Persistence ---
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_ops"
    redis_url: str = "redis://localhost:6379/0"

    # --- Auth ---
    jwt_secret_key: str = "change-me-in-local-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


# ============================================================
# Accessor
# ============================================================

@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance (FastAPI dependency pattern)."""
    return Settings()