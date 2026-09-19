"""Demo user store.

NOTE: In-memory on purpose — this is a portfolio auth demo, not an identity
platform (ADR-003). Passwords are bcrypt-hashed. Swap for a users table later
without touching endpoint code.
"""

from app.core.security import hash_password
from app.schemas.auth import Role

# ============================================================
# Demo users (username -> record)
# ============================================================


def _seed() -> dict[str, dict]:
    return {
        "admin": {
            "username": "admin",
            "hashed_password": hash_password("admin-pass-123"),
            "role": Role.ADMIN,
        },
        "dev": {
            "username": "dev",
            "hashed_password": hash_password("dev-pass-123"),
            "role": Role.DEVELOPER,
        },
        "user": {
            "username": "user",
            "hashed_password": hash_password("user-pass-123"),
            "role": Role.USER,
        },
    }


USERS: dict[str, dict] = _seed()


def get_user(username: str) -> dict | None:
    return USERS.get(username)
