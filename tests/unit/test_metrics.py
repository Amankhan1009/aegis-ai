"""Unit tests for AI cost estimation."""

from app.observability.metrics import (
    DEFAULT_PRICING,
    MODEL_PRICING,
    estimate_cost_usd,
)


def test_configured_model_uses_configured_pricing() -> None:
    model = "openai/gpt-oss-120b"

    cost = estimate_cost_usd(
        model=model,
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )

    input_price, output_price = MODEL_PRICING[model]
    assert cost == input_price + output_price


def test_unknown_model_uses_default_pricing() -> None:
    cost = estimate_cost_usd(
        model="unknown-model",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )

    input_price, output_price = DEFAULT_PRICING
    assert cost == input_price + output_price


def test_cost_is_rounded_to_eight_decimal_places() -> None:
    cost = estimate_cost_usd(
        model="openai/gpt-oss-120b",
        input_tokens=1,
        output_tokens=2,
    )

    assert cost == 0.0000007
