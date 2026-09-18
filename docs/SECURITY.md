# Security

&gt; Status: **In progress** — authn/authz (M5), audit trail (M14) implemented.

## Authentication
- JWT (HS256) access tokens, expiry from config (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- bcrypt password hashing (passlib).
- Demo user store in-memory (ADR-003) — swap for DB-backed users without
  touching endpoint code.

## Authorization (RBAC)
- Roles: ADMIN &gt; DEVELOPER &gt; USER.
- `require_roles(...)` dependency factory enforces least privilege per endpoint.
- Audit reads (`GET /api/v1/audit/events`) are ADMIN-only.

## Audit & governance (Milestone 14)
- Every AI request writes audit_events rows: attempt, success/failure,
  cache hit, idempotency replay.
- Fields: actor, action, resource, outcome, request_id, metadata (safe
  operational fields only — no prompts/secrets), timestamp.
- Audit write failures are logged, never raised (fail-safe).

## Secrets
- All secrets via env/.env (never committed). JWT secret ≥32 chars random.
- Groq key, DATABASE_URL, REDIS_URL read via pydantic-settings only.