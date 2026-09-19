# Failure Demonstration

## Milestone 20 — Final Failure Demonstration

AegisAI uses controlled failure injection to demonstrate how the platform
handles AI-provider failures and malformed AI output without affecting the
real Groq API.

Failure injection is intended for local/demo use and is activated through the
`X-Fail-Mode` request header.

---

## Scenario 1 — Invalid Structured Output

**Failure mode:** `invalid`

**Request ID:**

`05f22ad8-c297-494f-bca0-0fbf2df19b87`

### Observed behavior

- Controlled fallback response returned.
- `validation_failed=true`.
- Invalid-output metric increased.
- Audit event recorded `fail_mode="invalid"`.
- Audit outcome was `success` because the platform successfully handled the
  invalid output through its controlled fallback path.

### Observed metric

```text
aiops_requests_total{endpoint="ai.process",status="200"} 1.0
aiops_llm_invalid_output_total 2.0
```

---

## Scenario 2 — Simulated Provider HTTP 500

**Failure mode:** `error_500`

**Request ID:**

`f6beba90-4b6f-48a7-b63e-6d4bf07ecfb6`

### Observed behavior

- Simulated provider HTTP 500 failure triggered.
- Controlled fallback response returned.
- Initial attempt was followed by 2 retries.
- LLM error metric increased.
- Audit event recorded `fail_mode="error_500"`.

### Observed metrics

```text
aiops_retries_total{operation="ai.model_call"} 2.0
aiops_llm_requests_total{model="openai/gpt-oss-120b",outcome="error",provider="groq"} 1.0
```

---

## Scenario 3 — Simulated Provider HTTP 429 / Rate Limit

**Failure mode:** `rate_limit`

**Request ID:**

`60a8294c-a575-498c-b0ea-93e9f98b5943`

### Observed behavior

- Simulated provider HTTP 429 failure triggered.
- Controlled fallback response returned.
- Initial attempt was followed by 2 retries.
- LLM error metric increased.
- Audit event recorded `fail_mode="rate_limit"`.

### Final observed metrics

```text
aiops_requests_total{endpoint="ai.process",status="200"} 2.0
aiops_retries_total{operation="ai.model_call"} 4.0
aiops_llm_requests_total{model="openai/gpt-oss-120b",outcome="error",provider="groq"} 2.0
```

The retry counter reached `4.0` because Scenario 2 produced 2 retries and
Scenario 3 produced 2 additional retries.

The application-level rate-limit metric remained:

```text
aiops_rate_limit_hits_total 0.0
```

This metric represents AegisAI's own rate-limiting mechanism and is separate
from the simulated provider HTTP 429 failure.

---

## Audit Evidence

The following audit events were recorded:

| Request ID | Failure Mode | Outcome | Validation Failed |
|---|---|---|---|
| `05f22ad8-c297-494f-bca0-0fbf2df19b87` | `invalid` | `success` | `true` |
| `f6beba90-4b6f-48a7-b63e-6d4bf07ecfb6` | `error_500` | `success` | `false` |
| `60a8294c-a575-498c-b0ea-93e9f98b5943` | `rate_limit` | `success` | `false` |

The `success` audit outcome means AegisAI successfully handled the injected
failure through its controlled processing path. It does not mean that the
simulated provider operation succeeded.

---

## Failure Handling Flow

The demonstrated processing flow is:

```text
Failure Injection
       ↓
Failure Detection
       ↓
Retry Classification
       ↓
Retry + Exponential Backoff
       ↓
Controlled Fallback
       ↓
Structured Logging
       ↓
Prometheus Metrics
       ↓
Audit Event
       ↓
Operations Dashboard
```

---

## Retry Instrumentation

Retry observability was added so that actual retry attempts are exposed
through the Prometheus metric:

```text
aiops_retries_total{operation="ai.model_call"}
```

The metric increments when a retryable failure causes another attempt to be
scheduled.

For the demonstrated provider failures:

```text
Scenario 2:
2 retries

Scenario 3:
2 retries

Combined:
4 retries
```

---

## Automated Verification

The complete test suite was executed after the retry instrumentation changes.

```text
41 passed
11 warnings
3.89s
```

The warnings were dependency deprecation warnings and did not cause test
failures.

---

## Scenario Summary

| Scenario | Failure Mode | Fallback | Retries | Audit Evidence |
|---|---|---:|---:|---|
| 1 | `invalid` | Yes | Validation retry | `fail_mode=invalid` |
| 2 | `error_500` | Yes | 2 | `fail_mode=error_500` |
| 3 | `rate_limit` | Yes | 2 | `fail_mode=rate_limit` |

---

## Milestone Status

**Milestone 20: Verified**

The three required controlled failure scenarios were executed successfully.

The following behavior was verified:

- Controlled failure injection
- Invalid AI output handling
- Provider 500 handling
- Provider 429 handling
- Retry behavior
- Exponential backoff
- Controlled fallback
- LLM error metrics
- Retry metrics
- Audit records
- Failure-mode evidence
- Automated test coverage

Final automated verification:

```text
41 passed
```
