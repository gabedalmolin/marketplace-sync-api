# Marketplace Sync API

An incremental FastAPI service designed to receive marketplace order events, persist orders, prevent duplicate processing, and synchronize them with an external service.

The project is intentionally incremental. The current phase establishes a reproducible foundation and a tested health endpoint before introducing persistence and integration behavior.

## Current status

Phase A is complete:

- Python 3.12 environment managed by `uv`
- FastAPI application bootstrap
- Pydantic response contract
- `GET /health`
- pytest test infrastructure
- Ruff linting and formatting
- Runtime-focused Docker image
- Docker Compose with PostgreSQL
- Container and database health checks

Database persistence, webhooks, order operations, and external synchronization are not implemented yet.

## API

### Implemented

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Confirms that the API process is running |

Example response:

```json
{
  "status": "ok",
  "service": "marketplace-sync-api"
}
```

### Planned scope

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/webhooks/orders` | Receive an order event idempotently |
| `GET` | `/orders` | List persisted orders |
| `GET` | `/orders/{order_id}` | Retrieve one order |
| `POST` | `/orders/{order_id}/sync` | Synchronize an order with an external service |

## Technology stack

- Python 3.12
- uv
- FastAPI
- Pydantic v2
- SQLAlchemy 2 with asyncio support
- asyncpg
- PostgreSQL
- Alembic
- HTTPX
- pytest and pytest-asyncio
- Ruff
- Docker and Docker Compose

## Project structure

```text
app/
├── api/             # HTTP routes
├── core/            # Application configuration and shared concerns
├── db/
│   └── models/      # SQLAlchemy models
├── repositories/    # Persistence operations
├── schemas/         # Pydantic API contracts
├── services/        # Business and integration workflows
└── main.py          # FastAPI application composition

tests/
├── conftest.py      # Shared test fixtures
└── test_health.py   # Health endpoint behavior
```

Only files required by the current phase are implemented. Future modules will be added when their behavior is introduced.

## Local development

### Prerequisites

- Python 3.12+
- uv 0.12+
- Docker Desktop, for the containerized environment

### Install dependencies

```bash
uv sync
```

### Start the API locally

```bash
uv run fastapi dev app/main.py
```

The API will be available at:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Verify the endpoint:

```bash
curl -i http://127.0.0.1:8000/health
```

## Containerized environment

Create the local environment file:

```bash
cp .env.example .env
```

Build and start the API and PostgreSQL:

```bash
docker compose up --build --wait
```

Check service health:

```bash
docker compose ps
```

Verify the API:

```bash
curl -i http://127.0.0.1:8000/health
```

Stop the services while preserving PostgreSQL data:

```bash
docker compose down
```

Do not use `docker compose down --volumes` unless deleting local database data is intentional.

## Quality checks

Run the complete local quality gate:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
docker compose config --quiet
```

## Design decisions and trade-offs

### Incremental architecture

The repository defines clear boundaries for HTTP, schemas, persistence, and business workflows, but does not create empty implementations for future features. Modules are introduced only when they have real behavior.

### Root application layout

The application uses `app/` directly at the repository root instead of a packaged `src/` layout. This keeps a small service easy to navigate. Pytest explicitly includes the project root in its import path.

A packaged `src/` layout would become preferable if the codebase were published as a library or grew into a larger workspace.

### Explicit response contracts

The health endpoint returns a Pydantic model. This provides runtime validation, editor support, JSON Schema generation, and accurate OpenAPI documentation.

### Liveness versus readiness

`GET /health` is a liveness check. It confirms that the API process can respond and deliberately does not query PostgreSQL or external services.

Docker Compose defines separate infrastructure health checks. A dedicated readiness endpoint can be introduced later if deployment requirements justify it.

### Reproducible environments

`pyproject.toml` declares dependency constraints, while `uv.lock` records exact resolved versions. The Docker build validates the lockfile and excludes development-only dependencies.

### Database as the idempotency authority

The planned webhook flow will enforce a unique constraint on `event_id`. Application-level checks may improve responses, but the database constraint will provide the concurrency-safe guarantee.

## Next phase

Phase B will introduce:

1. Typed application settings
2. Async SQLAlchemy engine and session lifecycle
3. Order and webhook-event models
4. Alembic initialization and first migration
5. PostgreSQL integration tests

The webhook and external synchronization flows will only be implemented after the persistence boundary is tested.
