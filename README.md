# AegisAI — Enterprise AI Operations Platform

A production-style AI operations platform that demonstrates secure, reliable,
observable, cost-aware, and testable AI service delivery.

AegisAI uses FastAPI for the backend, Groq for AI inference, PostgreSQL for
operational data, Redis for caching and rate limiting, Prometheus metrics,
OpenTelemetry tracing, Streamlit operations dashboards, Docker Compose, and
GitHub Actions CI/CD.

## Core capabilities

- JWT authentication and role-based authorization
- Groq AI processing with `openai/gpt-oss-120b`
- Timeout, retry, exponential backoff, and circuit-breaker reliability controls
- Idempotency support for AI requests
- Redis caching and request rate limiting
- Structured JSON output validation and controlled fallback behavior
- Audit events for governance and administrative review
- Prometheus metrics and OpenTelemetry tracing
- Controlled failure injection for operational demonstrations
- Streamlit operations dashboard
- Docker Compose deployment
- Automated GitHub Actions linting, tests, Docker validation, and Docker Hub publishing

## Architecture

```text
Streamlit Dashboard
        |
        v
FastAPI Backend
        |
        +--> Groq AI Provider
        +--> PostgreSQL
        +--> Redis
        +--> Prometheus Metrics
        +--> OpenTelemetry Traces
```

## Live deployment

- **Frontend Dashboard:** https://aman-aegis-ai.streamlit.app
- **Backend API & Swagger Docs:** https://aegis-ai-api-u557.onrender.com/docs

## Quick start with Docker Compose

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Set at least these values:

```text
GROQ_API_KEY=your-groq-api-key
JWT_SECRET_KEY=use-a-long-random-secret-with-at-least-32-characters
```

Start the complete stack:

```bash
docker compose up --build
```

Open:

```text
Streamlit dashboard: http://localhost:8501
FastAPI API:         http://localhost:8000
FastAPI docs:        http://localhost:8000/docs
```

Stop the stack:

```bash
docker compose down
```

Remove local Docker database and Redis data only when intentionally resetting
the environment:

```bash
docker compose down -v
```

## Local development

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, start Streamlit:

```bash
streamlit run streamlit/app.py
```

## Demo users

These users are provided for local demonstration only.

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `admin-pass-123` |
| Developer | `dev` | `dev-pass-123` |
| User | `user` | `user-pass-123` |

Administrators can view audit events. Developers and users receive a clean
`403 Forbidden` response for that resource.

## API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/auth/login` | JWT login |
| `POST /api/v1/ai/process` | Process an AI request |
| `GET /api/v1/audit/events` | List audit events; administrator only |
| `GET /health` | Liveness probe |
| `GET /ready` | Readiness probe |
| `GET /metrics` | Prometheus metrics |

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

## Streamlit dashboard

The dashboard provides:

- Overview: request, cache, rate-limit, LLM, invalid-output, and estimated-cost metrics
- AI Operations: prompt execution, temperature, and structured output requests
- Failure Testing: controlled timeout, 500, rate-limit, invalid-output, and DB-timeout scenarios
- Audit Events: administrator-only event review and filtering
- System Health: liveness and readiness checks
- Metrics: Prometheus metric inspection

## Testing

Run formatting and lint checks:

```bash
.venv/bin/ruff format --check app/ streamlit/ tests/
.venv/bin/ruff check app/ streamlit/ tests/
```

Run the full unit and integration suite:

```bash
.venv/bin/pytest -v
```

Integration tests use an isolated PostgreSQL Testcontainers database. AI provider
calls are mocked, so tests do not consume Groq API quota.

## CI/CD

GitHub Actions runs on pushes and pull requests:

- formatting validation
- Ruff linting
- full pytest suite
- Docker Compose validation
- Docker image build validation

Successful pushes to `main` also publish API and Streamlit dashboard images to
Docker Hub with both `latest` and immutable Git SHA tags.

## Failure demonstration

Three controlled failure scenarios were verified:

- invalid structured output
- simulated provider 500 error
- simulated provider rate-limit error

See [FAILURE_DEMONSTRATION.md](docs/FAILURE_DEMONSTRATION.md) for the
recorded operational evidence.

## Documentation

- [Project roadmap](docs/PROJECT_ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contracts](docs/API_CONTRACTS.md)
- [Requirements](docs/REQUIREMENTS.md)
- [AI model strategy](docs/AI_MODEL_STRATEGY.md)
- [Reliability design](docs/RELIABILITY.md)
- [Failure scenarios](docs/FAILURE_SCENARIOS.md)
- [Failure demonstration](docs/FAILURE_DEMONSTRATION.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Operations runbook](docs/OPERATIONS_RUNBOOK.md)
- [Testing strategy](docs/TESTING_STRATEGY.md)
- [Changelog](docs/CHANGELOG.md)

