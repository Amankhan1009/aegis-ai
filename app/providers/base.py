"""Model provider abstraction (see docs/AI_MODEL_STRATEGY.md).

Business logic depends only on ModelProvider. Adding OpenAI/local later means
writing a new class that satisfies this interface — nothing else changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResult:
    content: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model: str
    raw: dict = field(default_factory=dict)


class ModelProvider(ABC):
    """Interface every AI provider must implement."""

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        timeout_seconds: float = 30.0,
    ) -> LLMResult:
        """Send a chat completion request. Must raise on failure (no swallowing)."""
