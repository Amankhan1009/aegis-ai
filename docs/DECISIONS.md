
### `docs/DECISIONS.md`
```markdown
# Architecture Decision Records (ADR)

## ADR-001: Monolithic modular FastAPI service (M0)
- Context: Portfolio project, single deployable unit is enough.
- Decision: One FastAPI app with clean internal modules; no microservices.
- Alternatives: microservices (rejected: over-engineering for scope).

## ADR-002: Hand-written reliability primitives (M0)
- Context: Retry/backoff/circuit breaker needed.
- Decision: Implement in `app/reliability/` (~small modules) instead of `tenacity`.
- Why: fully testable, transparent, demonstrates engineering; avoids a dependency
  whose semantics we'd need to disable/match anyway.
- Trade-off: we own the code; must be tested carefully (covered in Milestone 18).

## ADR-003: JWT + bcrypt for auth (M0)
- Context: Need authn/authz without building an identity platform.
- Decision: PyJWT access tokens + passlib/bcrypt hashing, roles ADMIN/DEVELOPER/USER.
- Alternatives: OAuth2/OIDC provider, sessions (rejected: unnecessary complexity for demo).

## ADR-004: Prometheus client + local scrape, OTel traces (M0)
- Context: Metrics/tracing must be free and local.
- Decision: prometheus-client metrics endpoint + OpenTelemetry SDK with console/OTLP exporter.
- Alternatives: SaaS observability (rejected: cost).

## ADR-005: Structlog for JSON logging (M0)
- Context: Structured logs required for debugging/audit.
- Decision: structlog with JSON renderer; request_id bound per request.
- Alternatives: stdlib logging + custom formatter (viable fallback; structlog chosen for ergonomics).

> New decisions are appended here as milestones land. Status: Proposed until M0 verified.