"""Redis client with graceful degradation.

If Redis is down, rate limiting fails OPEN (allow + log warning) and caching
is skipped — the app keeps working. Policy documented in docs/RELIABILITY.md.
"""

import redis

from app.core.config import get_settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    """Return the shared client, or None if Redis is unreachable."""
    global _client
    if _client is None:
        try:
            _client = redis.Redis.from_url(get_settings().redis_url, socket_timeout=2)
            _client.ping()
        except redis.RedisError:
            _client = None
    return _client