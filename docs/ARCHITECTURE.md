# Architecture

&gt; Status: **Designed** (implementation starts at Milestone 1/3).

## Layers
Client
│  HTTPS + JWT
▼
┌─────────────────────────────────────────────┐
│ FastAPI (app/api)                            │
│  middleware: request-id → auth → rate-limit  │
│  routes: /health /ready /api/v1/ai/process   │
└──────────────┬──────────────────────────────┘
▼
┌─────────────────────────────────────────────┐
│ Services (app/services)                      │
│  AI Orchestrator: validate → cache? →        │
│  idempotency → reliability wrap → provider   │
│  → output validation → persist → audit       │
└──────┬───────────────────────┬───────────────┘
▼                       ▼
┌───────────────┐     ┌───────────────────────┐
│ Providers     │     │ Repositories          │
│ ModelProvider │     │ (app/repositories)    │
│  └── Groq     │     │ requests / ai_usage / │
│       (gpt-oss-120b)│ workflows / failures / │
└───────────────┘     │ audit_events → PostgreSQL
└───────────────────────┘
Cross-cutting: reliability (timeout/retry/breaker) · observability (logs/metrics/traces)
Side systems: Redis (cache + rate limit) · Streamlit dashboard · Alembic migrations

## Key decisions
- Business logic never imports Groq directly; it depends on the `ModelProvider` interface.
- Redis failure must degrade gracefully (rate limit falls back to allow+warn or deny-open per policy in Milestone 9).
- Request ID (correlation ID) generated per request, propagated to logs, DB, traces.
- See docs/DECISIONS.md for recorded architecture decisions (ADRs).