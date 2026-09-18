# Failure Scenarios

&gt; Status: **Implemented** (Milestone 15) — injection via `X-Fail-Mode` header.

## Injection modes (local only, never in production)
| Mode | Simulates | Expected behavior |
|------|-----------|-------------------|
| `timeout` | LLM slower than 30s timeout | retry ×3 → fallback, failure recorded |
| `error_500` | LLM internal error | retry ×3 (5xx is retryable) → fallback |
| `rate_limit` | LLM 429 | retry ×3 (429 is retryable) → fallback |
| `invalid` | Malformed LLM output | validation retry ×1 → fallback `validation_failed=true` |
| `db_timeout` | Database failure on commit | error propagates (500), failure recorded |

## Chain demonstrated
Failure → Detection (retry classifier) → Retry (backoff) → Circuit breaker
→ Fallback → Structured log → Metric (`aiops_llm_requests_total{outcome=...}`)
→ failures table row → Dashboard (M16).

## Usage
```bash
curl -X POST localhost:8000/api/v1/ai/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Fail-Mode: error_500" \
  -d '{"prompt": "test"}'