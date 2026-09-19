# Operations Runbook

## Purpose

This runbook describes how to operate, verify, and troubleshoot the local
Docker Compose deployment of AegisAI.

## Start and stop

Start all services:

    docker compose up --build

Start in the background:

    docker compose up --build -d

View service status:

    docker compose ps

View logs:

    docker compose logs -f

View backend logs only:

    docker compose logs -f api

Stop services while retaining PostgreSQL and Redis data:

    docker compose down

Reset local PostgreSQL and Redis data:

    docker compose down -v

## Health verification

Check FastAPI liveness:

    curl http://localhost:8000/health

Expected:

    {"status":"ok","service":"enterprise-ai-ops"}

Check FastAPI readiness:

    curl http://localhost:8000/ready

Expected:

    {"status":"ready"}

Open the dashboard:

    http://localhost:8501

Open API documentation:

    http://localhost:8000/docs

## Dashboard access

Use local demonstration accounts:

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `admin-pass-123` |
| Developer | `dev` | `dev-pass-123` |
| User | `user` | `user-pass-123` |

Use an administrator account to inspect audit events.

## Metrics inspection

View all Prometheus metrics:

    curl -s http://localhost:8000/metrics

View AegisAI operational metrics only:

    curl -s http://localhost:8000/metrics | rg "^aiops_"

Useful metric groups:

| Metric | Meaning |
|---|---|
| `aiops_requests_total` | AI endpoint request outcomes |
| `aiops_retries_total` | Reliability retry attempts |
| `aiops_circuit_breaker_trips_total` | Circuit-breaker trips |
| `aiops_rate_limit_hits_total` | API rate-limit rejections |
| `aiops_cache_hits_total` | Redis cache hits |
| `aiops_cache_misses_total` | Redis cache misses |
| `aiops_llm_requests_total` | LLM outcomes by provider and model |
| `aiops_llm_tokens_total` | Input and output token usage |
| `aiops_llm_invalid_output_total` | Structured-output validation failures |
| `aiops_estimated_cost_usd_total` | Estimated model spend |

## Failure testing

Use the Streamlit **Failure Testing** page for local or demonstration
environments only.

Available modes:

| Mode | Simulates |
|---|---|
| `timeout` | Slow provider timeout |
| `error_500` | Provider internal error |
| `rate_limit` | Provider 429 response |
| `invalid` | Invalid structured model output |
| `db_timeout` | Database timeout scenario |

Failure injection sends the `X-Fail-Mode` request header. Never expose failure
testing controls in a production environment.

For expected behavior and final evidence, see:

- [Failure scenarios](FAILURE_SCENARIOS.md)
- [Final failure demonstration](FAILURE_DEMONSTRATION.md)

## Common troubleshooting

### Dashboard cannot connect to API

Check that the API container is running:

    docker compose ps api
    docker compose logs api

Confirm the health endpoint responds:

    curl http://localhost:8000/health

### AI requests fail unexpectedly

Check API logs:

    docker compose logs --tail=200 api

Confirm `GROQ_API_KEY` is present in `.env` and valid. Do not print or commit
the key.

### Database or Redis is unavailable

Check dependent service status:

    docker compose ps postgres redis
    docker compose logs postgres
    docker compose logs redis

Restart the stack:

    docker compose down
    docker compose up --build

### Port already in use

Check which local process uses the port:

    lsof -n -P -iTCP:8000 -sTCP:LISTEN
    lsof -n -P -iTCP:8501 -sTCP:LISTEN

Stop the conflicting process or change the host-side port mapping in
`docker-compose.yml`.

## Security notes

- Keep `.env` out of Git.
- Use a strong `JWT_SECRET_KEY`.
- Use Docker Hub access tokens only through GitHub Actions secrets.
- Do not use seeded demonstration credentials outside local development.
- Treat audit events, logs, and metrics as operational data.

