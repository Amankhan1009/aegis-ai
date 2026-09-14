# Enterprise AI Operations Platform

A production-style AI Operations platform demonstrating how an AI application can be
**Secure · Reliable · Observable · Cost-aware · Testable · Deployable**.

&gt; Status: **Milestone 0 — Planning**. The application is not implemented yet.
&gt; See `docs/PROJECT_ROADMAP.md` for the milestone plan.

## Planned highlights
- FastAPI service layer with JWT auth, RBAC, request validation, request IDs
- Provider-agnostic AI layer (initially Groq `openai/gpt-oss-120b`)
- Timeouts, retries with backoff, circuit breaker, graceful fallback, idempotency
- PostgreSQL persistence · Redis caching/rate limiting
- Structured logs, Prometheus metrics, OpenTelemetry traces
- Token usage + estimated AI cost tracking
- Streamlit operations dashboard, failure injection, audit trail
- Docker Compose, pytest suite, GitHub Actions CI

## Docs
See the `docs/` directory.