"""AI output validation & guardrails.

Strategy (documented in docs/RELIABILITY.md):
1. If the request asks for structured output, the model is instructed to reply
   with ONLY JSON matching the given schema description.
2. We parse the JSON and validate required fields + allowed values.
3. On invalid output: one retry with an explicit correction prompt.
4. If still invalid: return a controlled fallback + increment invalid-output metric.
"""

import json
import re

from pydantic import BaseModel

from app.observability.logging import get_logger

log = get_logger("ai.validation")

MAX_OUTPUT_CHARS = 8000  # guardrail: reject absurdly long outputs


class StructuredOutputSpec(BaseModel):
    """What the caller expects back."""

    required_fields: list[str]
    allowed_values: dict[str, list[str]] | None = None  # field -> allowed values


class OutputValidationError(Exception):
    """Raised when output fails validation (carries reason)."""


def _extract_json(text: str) -> dict:
    """Tolerate markdown fences: find the first {...} block and parse it."""
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise OutputValidationError("no JSON object found in output")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise OutputValidationError(f"malformed JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise OutputValidationError("JSON is not an object")
    return data


def validate_structured_output(raw: str, spec: StructuredOutputSpec) -> dict:
    """Validate LLM output against the spec. Raises OutputValidationError."""
    if len(raw) > MAX_OUTPUT_CHARS:
        raise OutputValidationError("output exceeds size limit")

    data = _extract_json(raw)

    missing = [f for f in spec.required_fields if f not in data]
    if missing:
        raise OutputValidationError(f"missing required fields: {missing}")

    if spec.allowed_values:
        for field, allowed in spec.allowed_values.items():
            if field in data and data[field] not in allowed:
                raise OutputValidationError(
                    f"field '{field}' value {data[field]!r} not in allowed {allowed}"
                )
    return data


def build_correction_prompt(original_prompt: str, spec: StructuredOutputSpec, error: str) -> str:
    """Prompt used for the single structured-output retry."""
    return (
        f"{original_prompt}\n\n"
        f"Your previous reply failed validation: {error}.\n"
        f"Reply with ONLY a JSON object containing these fields: {spec.required_fields}."
    )