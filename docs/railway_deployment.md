# Railway Deployment (Public Replay Platform)

This document describes how to deploy the public replay platform (FastAPI + PostgreSQL + Alembic) to Railway using the repository Dockerfile.

## What Gets Deployed

- FastAPI service (`uvicorn lilith_replay_core.api.app:app`)
- PostgreSQL database (Railway managed Postgres)
- Alembic migrations (run automatically at container start)

## Prerequisites

- Railway project created for this repository
- A Railway Postgres database added to the project

## Build / Runtime Model

- `railway.json` uses `builder: DOCKERFILE`
- The Docker image installs `.[db,api]` extras by default and includes `alembic.ini` + `alembic/`
- Container start command runs:
  - `alembic upgrade head`
  - then starts the API server

If migrations fail, the process exits and the service does not start (fail-closed).

## Environment Variables

Required:

- `DATABASE_URL` (Railway provides this automatically when a Postgres service is attached)

Recommended:

- `APP_ENV=production`
- `LOG_LEVEL=INFO`
- `ENABLE_METRICS=1`
- `API_HOST=0.0.0.0`

Railway Port:

- Railway provides `PORT`. The Docker entrypoint uses `PORT` to bind Uvicorn.
  - Railway typically provides `DATABASE_URL` with a `postgresql://` scheme; the application normalizes this to the SQLAlchemy psycopg driver automatically.

## PostgreSQL Attachment

1. Add a Postgres plugin/service to the Railway project.
2. Ensure the service exposes `DATABASE_URL` to the web service (default Railway behavior).
3. Confirm `/health/db` is enabled by `DATABASE_URL` being present.

## Deployment Steps

1. Connect Railway to the GitHub repository.
2. Use the default Dockerfile build (no custom build command needed).
3. Add/verify environment variables:
   - `APP_ENV=production`
   - `LOG_LEVEL=INFO`
   - `ENABLE_METRICS=1`
4. Deploy.
5. Verify endpoints:
   - `/health`
   - `/health/db`
   - `/docs`
   - `/metrics` (if enabled)

## Troubleshooting

### Migrations fail at startup

- The service will not start if `alembic upgrade head` fails.
- Check service logs for the Alembic failure output.
- Common causes:
  - `DATABASE_URL` missing or invalid
  - database not reachable
  - database permissions insufficient for schema creation

### /health/db returns UNKNOWN migration status

- The endpoint reports `migration_status=UNKNOWN` if it cannot determine the repository head revision.
- Ensure the container image includes `alembic.ini` + `alembic/` and that Alembic is installed.

### Multiple instances / scaling

- Running migrations on every start can be problematic if multiple instances start at the same time.
- Recommended approach for scaling:
  - keep a single instance during deploy/migration, then scale after migration completes.
