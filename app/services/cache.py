"""Response cache for AI calls.

Cache key = SHA256(provider + model + prompt + system_prompt + temperature).
TTL 15 minutes. Never caches: fallback responses, error responses, or anything
with output_tokens == 0 (our fallback marker). Sensitive data policy: we cache
LLM outputs keyed by content hash — no user identifiers in the key.
"""

import hashlib
import json

from app.core.config import get_settings
from app.core.redis_client import get_redis
from app.schemas.ai import AIProcessRequest, AIProcessResponse

TTL_SECONDS = 900


def _key(payload: AIProcessRequest) -> str:
    settings = get_settings()
    raw = "|".join(
        [
            settings.ai_provider,
            settings.ai_model,
            payload.prompt,
            payload.system_prompt or "",
            str(payload.temperature),
        ]
    )
    return "ai:cache:" + hashlib.sha256(raw.encode()).hexdigest()


def get(payload: AIProcessRequest) -> AIProcessResponse | None:
    r = get_redis()
    if r is None:
        return None
    data = r.get(_key(payload))
    if data is None:
        return None
    return AIProcessResponse(**json.loads(data))


def set(payload: AIProcessRequest, response: AIProcessResponse) -> None:
    """Store a successful, non-fallback response."""
    if response.output_tokens == 0:  # fallback marker — never cache
        return
    r = get_redis()
    if r is None:
        return
    r.setex(_key(payload), TTL_SECONDS, json.dumps(response.model_dump()))
