"""Fixed-window rate limiting per user per endpoint.

Default: 10 requests/minute per user on /ai/process (generous for dev; tuned
in production config). Uses INCR+EXPIRE — atomic enough for a portfolio demo.
"""

from fastapi import HTTPException, Request, status

from app.core.redis_client import get_redis

LIMIT = 10  # requests
WINDOW_SECONDS = 60


def check_rate_limit(request: Request, username: str, endpoint: str = "ai.process") -> None:
    """Raise 429 if the user exceeded the limit. Fails open if Redis is down."""
    r = get_redis()
    if r is None:
        return  # degraded: allow (documented policy)

    key = f"rl:{endpoint}:{username}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, WINDOW_SECONDS)
    if count > LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {LIMIT} requests per {WINDOW_SECONDS}s",
        )
