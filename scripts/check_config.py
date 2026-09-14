"""Verify that configuration loads correctly from .env.

Prints every setting with secrets masked. Exits non-zero if the JWT secret
is still the unsafe default — a cheap guard against shipping bad config.
"""

import sys
from pathlib import Path

# Allow running as: python scripts/check_config.py from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings

# ============================================================
# Helpers
# ============================================================

def mask(name: str, value: str) -> str:
    """Mask likely-secret values; show safe values as-is."""
    if not value:
        return "(not set)"
    if any(token in name for token in ("key", "secret", "password")):
        return f"****{value[-4:]} ({len(value)} chars)"
    return value


# ============================================================
# Main
# ============================================================

def main() -> int:
    settings = get_settings()

    print("Configuration loaded from environment/.env:\n")
    for name, value in sorted(settings.model_dump().items()):
        print(f"  {name:<28} = {mask(name, str(value))}")

    if settings.jwt_secret_key == "change-me-in-local-env":
        print("\nWARNING: JWT_SECRET_KEY is still the default value.")
        return 1

    if not settings.groq_api_key:
        print("\nNOTE: GROQ_API_KEY not set (fine until Milestone 6).")

    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())