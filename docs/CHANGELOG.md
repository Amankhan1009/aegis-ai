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
