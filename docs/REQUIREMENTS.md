# Requirements

## Functional
- F1: Authenticated AI processing endpoint `POST /api/v1/ai/process`.
- F2: Role-based access (ADMIN / DEVELOPER / USER) with least privilege.
- F3: Request validation via Pydantic schemas.
- F4: Idempotent request handling via Idempotency-Key header.
- F5: Health (`/health`) and readiness (`/ready`) endpoints.
- F6: Rate limiting (Redis-backed) per user/endpoint.
- F7: Caching of suitable AI responses with TTL.
- F8: Audit trail of important actions (who/what/when/request_id/result).
- F9: Token usage + estimated cost tracking per request.
- F10: AI output validation against a schema with retry/fallback on invalid output.
- F11: Failure injection hooks for controlled local testing.
- F12: Streamlit operations dashboard (no secrets exposed).

## Non-functional
- NF1: Every external call (LLM, DB, Redis) has a timeout.
- NF2: Retries with exponential backoff only on retryable errors; bounded retry count.
- NF3: Circuit breaker around the LLM provider; graceful fallback response.
- NF4: Structured JSON logs with request_id correlation on every operation.
- NF5: Metrics: request counts, latency (p95), retries, breaker trips, rate-limit events,
  cache hit/miss, LLM tokens, invalid-output rate, estimated cost.
- NF6: OpenTelemetry traces across HTTP → auth → workflow → DB → LLM.
- NF7: Provider-agnostic AI layer: switch provider/model via env vars only.
- NF8: PostgreSQL via DATABASE_URL; migrations via Alembic. No hardcoded credentials.
- NF9: Automated tests never call the real LLM (mocked). CI runs lint + tests + Docker build.
- NF10: All local infrastructure via Docker Compose. Target dev cost: ₹0.