"""Prometheus metrics (prometheus-client).

Exposed at /metrics (Milestone 11 wiring). Counters/histograms follow
naming: aiops_<domain>_<name>_<unit>.
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# ============================================================
# HTTP / operations
# ============================================================

REQUEST_COUNT = Counter("aiops_requests_total", "Total API requests", ["endpoint", "status"])
REQUEST_LATENCY = Histogram("aiops_request_latency_seconds", "Request latency", ["endpoint"])

RETRY_COUNT = Counter("aiops_retries_total", "Retry attempts", ["operation"])
BREAKER_TRIPS = Counter("aiops_circuit_breaker_trips_total", "Circuit breaker trips", ["name"])
RATE_LIMIT_HITS = Counter("aiops_rate_limit_hits_total", "Rate-limited requests")

CACHE_HITS = Counter("aiops_cache_hits_total", "Cache hits")
CACHE_MISSES = Counter("aiops_cache_misses_total", "Cache misses")

# ============================================================
# AI-specific
# ============================================================

LLM_REQUESTS = Counter("aiops_llm_requests_total", "LLM calls", ["provider", "model", "outcome"])
LLM_TOKENS = Counter("aiops_llm_tokens_total", "Tokens used", ["provider", "model", "kind"])
LLM_LATENCY = Histogram("aiops_llm_latency_seconds", "LLM call latency", ["provider", "model"])
LLM_INVALID_OUTPUT = Counter("aiops_llm_invalid_output_total", "Invalid LLM outputs")
ESTIMATED_COST_USD = Counter(
    "aiops_estimated_cost_usd_total", "Estimated AI spend (USD)", ["provider", "model"]
)


# ============================================================
# Cost model (documented estimates — see docs/AI_MODEL_STRATEGY.md)
# ============================================================

# USD per 1M tokens (input, output). Groq free-tier pricing placeholder —
# update from Groq's pricing page; clearly labeled as ESTIMATE.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "openai/gpt-oss-120b": (0.10, 0.30),
}

DEFAULT_PRICING: tuple[float, float] = (0.50, 1.50)


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimated cost in USD for a call. Clearly an estimate, not a bill."""
    in_price, out_price = MODEL_PRICING.get(model, DEFAULT_PRICING)
    return round((input_tokens / 1_000_000) * in_price + (output_tokens / 1_000_000) * out_price, 8)


# ============================================================
# Export
# ============================================================


def metrics_response() -> tuple[bytes, str]:
    """Return (payload, content_type) for the /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
