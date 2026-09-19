## Current Test Coverage — Milestone 18

The project uses both unit and integration tests.

### Unit tests

| Area | Test file | Coverage |
|---|---|---|
| Structured output validation | `tests/unit/test_validation.py` | Valid JSON, markdown JSON, missing fields, disallowed values, malformed JSON, non-JSON output, correction prompts |
| Failure injection | `tests/unit/test_failure_injection.py` | Normal pass-through, invalid output, simulated 500, simulated 429, timeout behavior |
| Metrics and cost estimation | `tests/unit/test_metrics.py` | Configured pricing, fallback pricing, cost rounding |
| Circuit breaker | `tests/unit/test_circuit_breaker.py` | Closed, open, half-open, recovery, fast-fail, trip counting |
| Retry logic | `tests/unit/test_retry.py` | Retryable classification, non-retryable failures, exponential backoff, capped delay, final failure |
| Reliability composition | `tests/unit/test_decorators.py` | Successful calls, HTTP timeout conversion, open-circuit behavior |

### Integration tests

| Area | Test file | Coverage |
|---|---|---|
| Health endpoints | `tests/integration/test_health.py` | Liveness and readiness endpoints |
| Authentication | `tests/integration/test_auth.py` | Valid login and invalid credentials |
| Audit authorization | `tests/integration/test_audit.py` | Admin access and developer denial |
| AI processing | `tests/integration/test_ai_process.py` | Mocked provider response, structured output, controlled fallback, authentication, request validation |

### Test isolation

Integration tests use a disposable PostgreSQL container through Testcontainers.

- Tests do not use the local Docker Compose database.
- Tests do not use the Neon database.
- The Groq provider is mocked for AI endpoint tests.
- Tests do not consume Groq API quota.
- OpenTelemetry uses a no-op provider when `APP_ENV=test`.

### Running tests

Run the complete suite:

```bash
.venv/bin/pytest -v