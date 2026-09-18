# Observability

&gt; Status: **In progress** — structured logging implemented (M10); metrics (M11)
&gt; and tracing (M12) land next.

## Structured logging (Milestone 10)
- structlog, JSON renderer, one event per line.
- Every event carries: `timestamp`, `level`, `service` (logger name), `operation`,
  plus bound context `request_id` and `user`.
- Key events: request_started, cache_hit, cache_miss, idempotency_replay,
  model_call_completed, request_completed, request_failed.
- Fallback responses are logged via request_completed with status=success but
  output_tokens=0 (distinguishable in queries).

## Viewing logs
```bash
uvicorn app.main:app --port 8000 2&gt;&1 | jq .
# or filter:
... | jq 'select(.operation=="ai.process")'

## Metrics (Milestone 11)
- Endpoint: `GET /metrics` (Prometheus text format).
- Names: `aiops_requests_total`, `aiops_request_latency_seconds`,
  `aiops_retries_total`, `aiops_circuit_breaker_trips_total`,
  `aiops_rate_limit_hits_total`, `aiops_cache_hits_total`, `aiops_cache_misses_total`,
  `aiops_llm_requests_total`, `aiops_llm_tokens_total`, `aiops_llm_latency_seconds`,
  `aiops_llm_invalid_output_total`, `aiops_estimated_cost_usd_total`.
- Cost model: per-1M-token price table in `app/observability/metrics.py`
  (`MODEL_PRICING`). Values are ESTIMATES — update from the provider's pricing
  page; never treat as billing truth.

## Distributed tracing (Milestone 12)
- OpenTelemetry SDK; auto-instrumentation for FastAPI (parent span per request).
- Manual spans: `ai.process_endpoint` (user, idempotency key, tokens),
  `ai.model_call` (model, provider, tokens, latency, outcome).
- Exporter: console by default (spans in uvicorn logs). Set
  `OTEL_EXPORTER_OTLP_ENDPOINT=https://...` to send to Jaeger/Tempo/etc.
- request_id is propagated as the trace correlation anchor (same value in
  logs, spans, and DB rows).