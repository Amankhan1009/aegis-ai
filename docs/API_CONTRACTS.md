# API Contracts

&gt; Status: **In progress** — only system endpoints exist so far.

## Conventions
- Versioned business endpoints live under `/api/v1/...` (added from Milestone 6).
- Every response carries an `X-Request-ID` header (echoed if the client sends one).
- Every error body follows the `ErrorResponse` schema:

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "request_id": "3f6c...",
  "detail": []
}

## Auth endpoints (Milestone 5)

### POST /api/v1/auth/login — OAuth2 password flow
Form fields: `username`, `password`.
- 200: `{ "access_token": "&lt;jwt&gt;", "token_type": "bearer" }`
- 401: invalid credentials

Demo users (bcrypt-hashed, in-memory — see app/core/users.py):
| username | password | role |
|----------|----------|------|
| admin | admin-pass-123 | ADMIN |
| dev | dev-pass-123 | DEVELOPER |
| user | user-pass-123 | USER |

### GET /api/v1/me — any authenticated user
Header: `Authorization: Bearer &lt;token&gt;`.
- 200: `{ "username": "...", "role": "..." }`
- 401: missing/invalid/expired token

### GET /api/v1/admin-only — ADMIN role required
- 200: `{ "message": "admin access granted", "user": "..." }`
- 403: authenticated but wrong role

## AI endpoints (Milestone 6)

### POST /api/v1/ai/process — authenticated users
Headers: `Authorization: Bearer &lt;token&gt;`, `X-Request-ID` (optional).
Body:
```json
{
  "prompt": "Explain circuit breakers in two sentences.",
  "system_prompt": "You are a concise assistant.",
  "temperature": 0.7
}
- 200: AIProcessResponse (request_id, provider, model, output, tokens, latency)
- 401/403: auth failures
- 500: provider failure (reliability handling lands in M7)

### POST /api/v1/ai/process — idempotency (Milestone 8)
Optional header: `Idempotency-Key: <client-generated-uuid>`.
- First call with a key: normal processing; result stored against the key.
- Retry with same key: stored result returned (no LLM call, no extra tokens).
- Retry while original still running: `409 Conflict`.
- Failed original: key marked failed; a new key is required to re-execute.

### POST /api/v1/ai/process — rate limit & cache (Milestone 9)
- Rate limit: 10 requests/minute per user → `429` with retry hint.
- Cache: identical (provider, model, prompt, system_prompt, temperature) within
  15 min returns the stored response instantly (no LLM call, no tokens).
- Fallback responses are never cached.
- Redis outage: rate limit fails open (allow), cache skipped — app stays up.