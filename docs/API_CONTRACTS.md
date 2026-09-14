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