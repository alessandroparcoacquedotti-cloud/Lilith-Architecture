# Database (PostgreSQL + SQLAlchemy + Alembic)

This repository includes a public-safe persistence layer intended for production-style usage with PostgreSQL, SQLAlchemy 2.x, and Alembic migrations.

## Architecture

- The application uses SQLAlchemy 2.x typed ORM models.
- Migrations are managed by Alembic.
- Runtime configuration is environment-driven. Avoid committing credential-bearing configuration.

Key paths:

- Models: `src/lilith_replay_core/db/models.py`
- Declarative base + schema version: `src/lilith_replay_core/db/base.py`
- Session/engine helpers: `src/lilith_replay_core/db/session.py`
- Alembic config: `alembic.ini`, `alembic/env.py`, `alembic/versions/`

## Models

### ReplayRun

Represents a single replay execution run.

Fields:

- `run_id`: stable public-safe identifier (UUID, primary key)
- `created_at`: creation time
- `replay_type`: caller-provided run category (public-safe string)
- `status`: lifecycle status (`created | running | complete | failed`)
- `manifest_hash`: deterministic manifest hash used as a root-of-trust identifier
- `request_id`: request correlation identifier (from `X-Request-ID` / middleware)

### ArtifactRecord

Represents a persisted pointer to an audit/replay artifact produced by a run.

Fields:

- `artifact_id`: surrogate primary key
- `run_id`: foreign key to `ReplayRun.run_id`
- `artifact_type`: artifact category (public-safe string)
- `artifact_hash`: deterministic integrity hash
- `created_at`: creation time

Constraints and indexes:

- `ReplayRun.run_id` is a primary key.
- `ArtifactRecord` enforces uniqueness on `(run_id, artifact_type, artifact_hash)`.
- Indexes exist for run correlation and lookup fields.

## Local Setup (PostgreSQL)

With Docker Compose:

```bash
export POSTGRES_PASSWORD='your-dev-password'
docker compose up --build
```

The API container runs `alembic upgrade head` before starting the FastAPI server.

## Migration Workflow

Run migrations against a configured database:

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/DB'
alembic upgrade head
```

Create a new revision (autogenerate):

```bash
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/DB'
alembic revision --autogenerate -m "describe change"
```

## Health Check

`GET /health/db` verifies:

- database connectivity
- migration governance state (database revision vs repository head)

The response is deterministic JSON and does not include secrets.

## Migration Governance

`GET /health/db` reports:

- `database`: `PASS | FAIL` (connectivity only)
- `migration_status`: `UP_TO_DATE | OUTDATED | UNKNOWN`
- `database_revision`: revision recorded in the database (if available)
- `repository_head_revision`: the repository migration head (derived from Alembic)
- `request_id`: request correlation identifier

Interpretation:

- `UP_TO_DATE`: database revision matches the repository head.
- `OUTDATED`: database revision is missing or differs from repository head.
- `UNKNOWN`: the repository head cannot be determined (e.g., Alembic scripts not present or Alembic not installed).
