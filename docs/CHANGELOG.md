# Changelog

## Milestone 0 — Project Planning
- Created project folder skeleton.
- Added docs: roadmap, requirements, architecture, AI model strategy, ADRs, changelog.
- Proposed technology stack (pending approval).
## Milestone 1 — Project Foundation
- Added requirements.txt (runtime + dev/test sections, pinned ranges).
- Added package skeleton (__init__.py) for app and tests.
- Created local .venv and installed all dependencies.

## Milestone 2 — Configuration & Secrets
- Added app/core/config.py (pydantic-settings, lru_cache accessor).
- Added scripts/check_config.py (masked config dump + default-secret guard).
- Created local .env from .env.example (git-ignored).

## Milestone 3 — FastAPI Foundation
- Added app/main.py (app factory), app/api/health.py (/health, /ready).
- Added RequestIDMiddleware (X-Request-ID correlation).
- Added global error handlers + ErrorResponse schema (AppError, 422, 500).
- Documented /health, /ready in docs/API_CONTRACTS.md.

## Milestone 4 — PostgreSQL (Neon)
- Switched to Neon serverless PostgreSQL via DATABASE_URL (sslmode=require).
- Added app/core/database.py, 5 ORM models, Alembic setup; first migration applied to Neon.

## Milestone 5 — Authentication & Authorization
- Added app/core/security.py (bcrypt hashing, JWT create/decode).
- Added app/core/users.py (in-memory demo users, ADR-003).
- Added POST /api/v1/auth/login, GET /api/v1/me, GET /api/v1/admin-only.
- Added get_current_user dependency + require_roles factory.

## Milestone 6 — AI Service
- Added ModelProvider interface + GroqProvider + factory (provider-agnostic).
- Added POST /api/v1/ai/process with usage persistence to ai_usage table.

## Milestone 7 — Reliability Layer
- Added app/reliability/: retry.py (backoff+jitter, retryable classification),
  circuit_breaker.py (CLOSED/OPEN/HALF_OPEN, trip count), decorators.py (compose).
- AI service now wraps provider calls: breaker → retry → timeout; fallback on failure.

## Milestone 8 — Idempotency
- Added app/services/idempotency.py (claim/complete/fail on workflow_executions).
- POST /ai/process accepts Idempotency-Key; duplicates replay stored result (409 if in-flight).

## Milestone 9 — Caching & Rate Limiting
- Added app/core/redis_client.py (graceful degradation), services/rate_limit.py
  (10 req/min per user, fail-open), services/cache.py (SHA256 key, 15min TTL,
  fallback responses never cached).

## Milestone 10 — Structured Logging
- Added app/observability/: logging.py (structlog JSON), context.py (contextvars).
- RequestIDMiddleware binds request_id/user to every log line.
- ai.endpoint + ai.service emit structured events (started/completed/failed,
  cache hit/miss, idempotency replay, model_call_completed).

## Milestone 11 — Metrics
- Added app/observability/metrics.py (Prometheus counters/histograms + cost model).
- GET /metrics endpoint; ai endpoint/service emit request, cache, rate-limit,
  LLM token/latency/outcome, and estimated-cost metrics.

## Milestone 12 — Distributed Tracing
- Added app/observability/tracing.py (OTel SDK, console/OTLP exporter switch).
- Manual spans: ai.process_endpoint, ai.model_call (with token/latency attrs).
- FastAPI auto-instrumentation in main.py.

## Milestone 13 — AI Output Validation & Guardrails
- Added app/services/validation.py (JSON extraction, schema/allowed-value checks,
  size guardrail, correction-prompt builder).
- structured_output spec on POST /ai/process; single retry then fallback;
  aiops_llm_invalid_output_total metric.

## Milestone 14 — Audit & Governance
- Added app/services/audit.py (fail-safe audit writer).
- Added GET /api/v1/audit/events (ADMIN only) with actor/outcome filters.
- ai.process endpoint records attempt/success/failure/cache/replay events.

## Milestone 15 — Failure Injection
- Added app/services/failure_injection.py (X-Fail-Mode header: timeout,
  error_500, rate_limit, invalid, db_timeout).
- AI service records failures to failures table; endpoint passes fail_mode.

## Milestone 16 — Streamlit Operations Dashboard
- Added JWT login and session state for the token, username, and role.
- Added Overview, AI Operations, Failure Testing, Audit Events, System Health,
  Metrics, and Logout navigation backed by the existing FastAPI APIs.
- Added Prometheus metric summaries, role-aware audit error handling, and
  operator-friendly handling for API, network, timeout, authentication, and
  rate-limit errors.
- Verified locally with FastAPI and Streamlit, including login, navigation,
  health/readiness, metrics, admin/non-admin audit access, and invalid-output
  failure injection.

## Milestone 17 — Docker / Docker Compose
- Added backend and Streamlit Dockerfiles.
- Added Docker Compose services for FastAPI, Streamlit, PostgreSQL, and Redis.
- Added persistent PostgreSQL and Redis volumes plus service health checks.
- Configured the Streamlit container to call the internal API service.
- Verified the full stack locally with `docker compose up --build`, backend health/readiness endpoints, and dashboard login.

## Milestone 18 — Testing
- Added isolated PostgreSQL integration-test infrastructure using Testcontainers.
- Added health, readiness, authentication, authorization, audit, and AI endpoint integration tests.
- Mocked the AI provider for AI processing tests; no Groq API calls are made during tests.
- Added unit tests for structured-output validation, failure injection, cost estimation,
  circuit-breaker state transitions, retry/backoff behavior, and resilient-call composition.
- Added test-environment no-op OpenTelemetry tracing to avoid exporting spans during pytest.
- Verified the complete linted test suite locally.