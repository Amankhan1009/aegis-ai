"""Schemas for the AI processing endpoint."""

from pydantic import BaseModel, Field

from app.services.validation import StructuredOutputSpec


class AIProcessRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    system_prompt: str | None = Field(default=None, max_length=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    structured_output: StructuredOutputSpec | None = None  # M13: demand JSON


class AIProcessResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    output: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    structured_result: dict | None = None  # populated when validation succeeds
    validation_failed: bool = False  # True when retry also failed
