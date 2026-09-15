"""Provider factory — the ONLY place that maps AI_PROVIDER to a class."""

from app.core.config import get_settings
from app.providers.base import ModelProvider
from app.providers.groq_provider import GroqProvider

_PROVIDERS: dict[str, type[ModelProvider]] = {
    "groq": GroqProvider,
    # "openai": OpenAIProvider,   # future — add class + one line here
}


def get_provider() -> ModelProvider:
    name = get_settings().ai_provider.lower()
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown AI_PROVIDER '{name}'. Supported: {sorted(_PROVIDERS)}"
        )
    return _PROVIDERS[name]()