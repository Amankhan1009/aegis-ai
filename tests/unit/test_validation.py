"""Unit tests for structured AI output validation."""

import pytest

from app.services.validation import (
    OutputValidationError,
    StructuredOutputSpec,
    build_correction_prompt,
    validate_structured_output,
)


def test_valid_structured_output_passes() -> None:
    spec = StructuredOutputSpec(
        required_fields=["summary", "severity"],
        allowed_values={"severity": ["low", "medium", "high"]},
    )

    result = validate_structured_output(
        '{"summary": "Database latency increased.", "severity": "high"}',
        spec,
    )

    assert result == {
        "summary": "Database latency increased.",
        "severity": "high",
    }


def test_markdown_fenced_json_passes() -> None:
    spec = StructuredOutputSpec(required_fields=["summary"])

    result = validate_structured_output(
        '```json\n{"summary": "Healthy"}\n```',
        spec,
    )

    assert result == {"summary": "Healthy"}


def test_missing_required_field_fails() -> None:
    spec = StructuredOutputSpec(required_fields=["summary", "severity"])

    with pytest.raises(OutputValidationError, match="missing required fields"):
        validate_structured_output('{"summary": "Healthy"}', spec)


def test_disallowed_value_fails() -> None:
    spec = StructuredOutputSpec(
        required_fields=["severity"],
        allowed_values={"severity": ["low", "medium", "high"]},
    )

    with pytest.raises(OutputValidationError, match="not in allowed"):
        validate_structured_output('{"severity": "critical"}', spec)


def test_malformed_json_fails() -> None:
    spec = StructuredOutputSpec(required_fields=["summary"])

    with pytest.raises(OutputValidationError, match="malformed JSON"):
        validate_structured_output('{"summary": invalid}', spec)


def test_non_json_output_fails() -> None:
    spec = StructuredOutputSpec(required_fields=["summary"])

    with pytest.raises(OutputValidationError, match="no JSON object found"):
        validate_structured_output("This is ordinary text.", spec)


def test_correction_prompt_includes_validation_requirements() -> None:
    spec = StructuredOutputSpec(required_fields=["summary", "severity"])

    prompt = build_correction_prompt(
        "Summarize this incident.",
        spec,
        "missing required fields",
    )

    assert "Summarize this incident." in prompt
    assert "missing required fields" in prompt
    assert "summary" in prompt
    assert "severity" in prompt
