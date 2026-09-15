# Database Design

&gt; Status: **Implemented** (Milestone 4) — migrations applied locally.

## Connection
- Hosted on **Neon** (serverless PostgreSQL); connection string from `DATABASE_URL` with `sslmode=require`.

## Migrations
- Alembic, autogenerate from ORM metadata (`alembic/env.py` imports `app.models.*`).
- First migration: `create operational tables`.

## Tables
| Table | Purpose | Key columns |
|-------|---------|-------------|
| request_logs | one row per inbound API call | request_id (unique), endpoint, method, user_id, status_code, latency_ms |
| ai_usage | per-request AI usage | request_id, provider, model, input/output tokens, latency_ms, estimated_cost_usd |
| workflow_executions | idempotency anchor | idempotency_key (unique), status, result (JSONB), error |
| failures | failure records | operation, error_type, error_message, retry_count |
| audit_events | audit trail | actor, action, resource, outcome, metadata (JSONB) |

All tables have UUID PKs and `created_at` timestamps.