# Marketplace Sync API

An incremental FastAPI service designed to receive marketplace order events, persist orders, prevent duplicate processing, and synchronize them with an external service.

The project is developed in small, reviewable phases. Phase A established the HTTP and container foundation. Phase B added the persistence boundary, database migrations, integrity constraints, and PostgreSQL integration tests.

## Current status

### Phase A — application foundation

Completed:

- Python 3.12 environment managed by `uv`
- FastAPI application bootstrap
- Pydantic response contract
- `GET /health`
- pytest test infrastructure
- Ruff linting and formatting
- Runtime-focused Docker image
- Docker Compose with PostgreSQL
- Container and database health checks

### Phase B — persistence foundation

Completed:

- Typed application settings with Pydantic Settings
- Async SQLAlchemy engine and session factory
- PostgreSQL access through `asyncpg`
- Declarative SQLAlchemy models for orders and webhook events
- Deterministic database constraint names
- Alembic async migration environment
- Initial reversible schema migration
- Database drift verification with `alembic check`
- PostgreSQL integration tests with transaction rollback
- Migration assets included in the runtime image

The webhook routes, order query endpoints, repositories, business services, and external synchronization workflow are not implemented yet.

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
| `POST` | `/webhooks/orders` | Receive and persist an order event idempotently |
| `GET` | `/orders` | List persisted orders |
| `GET` | `/orders/{order_id}` | Retrieve one order |
| `POST` | `/orders/{order_id}/sync` | Synchronize an order with an external service |

## Persistence model

### Orders

The `orders` table stores the current state of each marketplace order.

Important constraints:

- UUID primary key
- Unique `(marketplace, external_order_id)` pair
- `NUMERIC(12, 2)` monetary value
- Non-negative total enforced by a check constraint
- Timezone-aware creation and update timestamps

### Webhook events

The `webhook_events` table records accepted event identifiers.

Important constraints:

- UUID primary key
- Globally unique `event_id`
- Foreign key to `orders`
- Restricted order deletion while webhook events reference it
- Timezone-aware receipt timestamp

The unique `event_id` constraint is the concurrency-safe authority for idempotency. Application-level checks may improve the HTTP response, but only the database constraint can resolve simultaneous inserts correctly.

## Technology stack

- Python 3.12
- uv
- FastAPI
- Pydantic v2
- Pydantic Settings
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
alembic/
├── env.py                 # Async migration environment
├── script.py.mako         # Migration file template
└── versions/              # Versioned schema changes

app/
├── api/                   # HTTP routes
├── core/
│   └── config.py          # Typed environment configuration
├── db/
│   ├── base.py            # Declarative base and naming conventions
│   ├── session.py         # Async engine and session lifecycle
│   └── models/
│       ├── order.py
│       └── webhook_event.py
├── repositories/          # Planned persistence operations
├── schemas/               # Pydantic API contracts
├── services/              # Planned business and integration workflows
└── main.py                # FastAPI application composition

tests/
├── integration/
│   ├── conftest.py
│   └── test_database_constraints.py
├── conftest.py
├── test_config.py
└── test_health.py
```

Modules are introduced when they gain real behavior. The repository exposes clear architectural boundaries without prematurely implementing unused abstractions.

## Local development

### Prerequisites

- Python 3.12+
- uv 0.12+
- Docker Desktop

### Configure the environment

Create the local environment file:

```bash
cp .env.example .env
```

The real `.env` file is ignored by Git. Only `.env.example` is versioned.

### Install dependencies

```bash
uv sync --locked
```

### Start PostgreSQL

```bash
docker compose up --detach postgres --wait
```

### Apply database migrations

```bash
uv run alembic upgrade head
```

Confirm the current revision and check for schema drift:

```bash
uv run alembic current
uv run alembic check
```

### Start the API locally

```bash
uv run fastapi dev app/main.py
```

The application will be available at:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Verify the health endpoint:

```bash
curl -i http://127.0.0.1:8000/health
```

Stop the containerized database while preserving its named volume:

```bash
docker compose down
```

Do not use `docker compose down --volumes` unless deleting local database data is intentional.

## Containerized environment

Build the runtime image:

```bash
docker compose build api
```

Start PostgreSQL:

```bash
docker compose up --detach postgres --wait
```

Apply migrations from the runtime image:

```bash
docker compose run --rm api /app/.venv/bin/alembic upgrade head
```

Start the API:

```bash
docker compose up --detach api --wait
```

Check service health:

```bash
docker compose ps
curl -i http://127.0.0.1:8000/health
```

Stop the services while preserving PostgreSQL data:

```bash
docker compose down
```

Migrations are intentionally not executed by the API startup command. Schema changes should run as an explicit release step instead of being attempted concurrently by multiple API replicas.

## Database migrations

Create a migration after changing SQLAlchemy models:

```bash
uv run alembic revision --autogenerate -m "describe the schema change"
```

Autogenerated migrations are proposals and must be reviewed before application.

Apply all pending migrations:

```bash
uv run alembic upgrade head
```

Inspect the active revision:

```bash
uv run alembic current
```

Detect model and schema differences:

```bash
uv run alembic check
```

Downgrades may delete schema objects or data. They must be reviewed and require an appropriate backup strategy outside local disposable environments.

## Quality checks

Run the standard local quality gate:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
docker compose config --quiet
```

PostgreSQL integration tests are skipped by default. Run them explicitly against the local migrated database:

```bash
docker compose up --detach postgres --wait
uv run alembic upgrade head
RUN_INTEGRATION_TESTS=1 uv run pytest tests/integration -v
docker compose down
```

The integration fixture refuses production and remote database hosts. Each test runs inside a transaction that is rolled back afterward.

## Design decisions and trade-offs

### Incremental architecture

The repository defines clear boundaries for HTTP, schemas, persistence, and business workflows. Behavior is introduced in small increments so each decision remains explainable, testable, and reviewable.

### Root application layout

The application uses `app/` directly at the repository root instead of a packaged `src/` layout. This keeps a small service easy to navigate. Pytest explicitly includes the project root in its import path.

A packaged `src/` layout would become preferable if the codebase were published as a library or grew into a larger workspace.

### Explicit response contracts

The health endpoint returns a Pydantic model. This provides runtime validation, editor support, JSON Schema generation, and accurate OpenAPI documentation.

### Liveness versus readiness

`GET /health` is a liveness check. It confirms that the API process can respond and deliberately does not query PostgreSQL or external services.

Docker Compose defines separate infrastructure health checks. A dedicated readiness endpoint can be introduced later if deployment requirements justify it.

### Typed configuration

Application configuration is loaded from environment variables and `.env` through Pydantic Settings.

`DATABASE_URL` is required and validated as a PostgreSQL DSN. Missing or invalid configuration fails early instead of producing a delayed database error.

### Async database lifecycle

The application creates one async engine per process and an `AsyncSession` per request or unit of work.

The session dependency manages resource lifetime but does not perform hidden commits. Business services will own transaction boundaries explicitly.

### Database integrity and idempotency

The database enforces primary keys, foreign keys, unique business identifiers, and valid monetary totals.

The webhook service may check for an existing event to produce a clearer response, but the unique `event_id` constraint remains the final concurrency-safe guarantee.

### Money representation

Monetary values use Python `Decimal` and PostgreSQL `NUMERIC(12, 2)`. Binary floating-point types are intentionally avoided because they cannot exactly represent many decimal currency values.

### Migration lifecycle

Alembic compares `Base.metadata` with the PostgreSQL schema and records applied revisions in `alembic_version`.

Migration files are included in the runtime image, but migrations remain an explicit operational step. This avoids coupling API process startup to schema changes.

### Reproducible environments

`pyproject.toml` declares dependency constraints, while `uv.lock` records exact resolved versions. Docker validates the lockfile and excludes development-only dependencies.

## Next phase

Phase C will implement the first complete persistence workflow:

1. Pydantic request and response schemas for order events
2. Order and webhook-event repositories
3. Explicit service-layer transaction boundaries
4. Idempotent `POST /webhooks/orders`
5. `GET /orders`
6. `GET /orders/{order_id}`

External synchronization with HTTPX, bounded retries, and backoff will follow after the persistence and API boundaries are working and tested.
