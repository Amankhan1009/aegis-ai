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
