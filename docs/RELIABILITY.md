# Reliability

&gt; Status: **Implemented** (Milestone 7).

## Policy
| Concern | Decision |
|---------|----------|
| Timeout | 30s per LLM attempt (passed to Groq SDK / httpx) |
| Retry | max 3 attempts, exponential backoff base 0.5s, cap 8s, ±25% jitter |
| Retryable | timeouts, connection errors, HTTP 429, HTTP 5xx |
| Non-retryable | 4xx validation/auth errors (fail fast) |
| Circuit breaker | threshold 3 failures, 20s recovery, half-open trial |
| Fallback | controlled message with request_id; tokens=0; HTTP 200 |

## Failure policy
- Breaker OPEN → immediate fallback (no provider call).
- Retries exhausted → fallback with reason recorded in logs (M10) and failures table (M15 wiring).
- Fallback responses are identifiable: `output_tokens == 0` and the fixed fallback text.

## Redis degradation policy (Milestone 9)
| Feature | Redis down behavior |
|---------|---------------------|
| Rate limit | Fail-open: allow request + warning log |
| Cache | Skip silently |

## AI output validation (Milestone 13)
- Optional `structured_output` spec: required fields + allowed values.
- Model must reply with JSON only; we tolerate markdown fences.
- Invalid → 1 retry with correction prompt → fallback with `validation_failed=true`.
- Guardrails: max output size (8000 chars), schema check, allowed-value check.
- Metric: `aiops_llm_invalid_output_total` counts each invalid event.