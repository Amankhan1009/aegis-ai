# Architecture

> Status: **Verified** — reflects the implemented architecture through Milestone 21.

## Layers

```text
Client
   │
   │ HTTPS + JWT
   ▼
┌─────────────────────────────────────────────┐
│ FastAPI (app/api)                           │
│                                             │
│ Middleware:                                 │
│   request-id → authentication → rate-limit │
│                                             │
│ Routes:                                     │
│   /health                                   │
│   /ready                                    │
│   /api/v1/ai/process                        │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│ Services (app/services)                     │
│                                             │
│ AI Orchestrator:                            │
│   validate → cache → idempotency            │
│   → reliability → provider                  │
│   → output validation → persist → audit     │
└───────────────┬─────────────────┬───────────┘
                │                 │
                ▼                 ▼
┌──────────────────────┐   ┌────────────────────────┐
│ Providers            │   │ Repositories           │
│                      │   │                        │
│ ModelProvider        │   │ app/repositories       │
│   └── Groq           │   │                        │
│       gpt-oss-120b   │   │ requests               │
│                      │   │ ai_usage               │
└──────────────────────┘   │ workflows              │
                           │ failures               │
                           │ audit_events            │
                           │          │             │
                           └──────────┼─────────────┘
                                      ▼
                                 PostgreSQL

Cross-cutting concerns:
- Reliability: timeout, retry, backoff, circuit breaker, fallback
- Observability: structured logs, metrics, OpenTelemetry traces

Side systems:
- Redis: caching and rate limiting
- Streamlit: operations dashboard
- Alembic: database migrations