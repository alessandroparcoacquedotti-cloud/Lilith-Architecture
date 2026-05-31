# RAILWAY_DATABASE_URL_AUDIT

Repository: `C:\workspace_lilith_public\_tmp_target\Lilith-Architecture`

Context (reported):
- PostgreSQL service exists in Railway
- Healthcheck fails before service becomes healthy
- Deployment logs show no application startup output

This audit focuses on what the container does at runtime with/without `DATABASE_URL`, and what can prevent Uvicorn from starting.

## Files Inspected

- [db/session.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/db/session.py)
- [alembic/env.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic/env.py)
- [Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile)
- [health.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/health.py)
- [alembic.ini](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic.ini)

## Startup Sequence (Container Runtime)

Source: [Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L40-L42)

At container start, the process is:

1) Docker `CMD` runs:

```sh
sh -c "alembic upgrade head && uvicorn lilith_replay_core.api.app:app --host ${API_HOST:-0.0.0.0} --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --no-access-log"
```

2) Because this uses `&&`, the sequence is strict:
- If `alembic upgrade head` exits non-zero (or is still running), `uvicorn ...` will not start.
- If `alembic upgrade head` succeeds (exit code 0), `uvicorn ...` starts.

3) Container-level `HEALTHCHECK` probes:

```text
http://localhost:${PORT|API_PORT|8000}/health
```

Source: [Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L40)

## Database URL Resolution Logic (Alembic)

### URL normalization
Source: [normalize_database_url](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/db/session.py#L15-L21)

- `postgres://...` becomes `postgresql+psycopg://...`
- `postgresql://...` becomes `postgresql+psycopg://...`
- Anything else is returned unchanged

This is important because Railway often provides `DATABASE_URL` as `postgresql://...` (or sometimes `postgres://...`), while SQLAlchemy + psycopg typically expects `postgresql+psycopg://...` for the psycopg3 driver.

### Alembic env chooses the DB URL in this order
Source: [_get_database_url](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic/env.py#L22-L29)

Order:
1) If `DATABASE_URL` is set and non-empty:
   - use `normalize_database_url(DATABASE_URL)`
2) Else, if `POSTGRES_HOST` is set:
   - use `build_postgres_url_from_env()`
3) Else:
   - fall back to `alembic.ini` `sqlalchemy.url`

The `alembic.ini` fallback value is:
- `sqlite:///./local.db` ([alembic.ini](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic.ini#L1-L4))

## Exactly What Happens When `DATABASE_URL` Exists

### Expected
1) `alembic upgrade head` runs migrations against the Postgres instance referenced by `DATABASE_URL`.
2) On success (exit code 0), Uvicorn starts and begins serving HTTP.

### Failure modes that prevent Uvicorn from ever starting
Because `alembic upgrade head` runs before Uvicorn and is chained via `&&`, any of these will keep the service from becoming healthy and can explain “no application startup output”:

- DB is unreachable at container start (DNS/network not ready, wrong host/port, security rules).
  - Alembic will block during connect or fail after a timeout; Uvicorn never starts.
- DB exists but credentials/URL are wrong.
  - Alembic fails fast or after connect attempt; Uvicorn never starts.
- DB is reachable but migration fails (permissions, schema conflicts, concurrent migration locking).
  - Alembic exits non-zero; Uvicorn never starts.

Result in all cases:
- Container keeps restarting or sits stuck at migrations, and Railway healthchecks to `/health` will fail because there is no listening web server yet.

## Exactly What Happens When `DATABASE_URL` Is Missing

Two distinct cases exist depending on whether `POSTGRES_HOST` is set.

### Case A: `DATABASE_URL` missing AND `POSTGRES_HOST` missing
Source: [_get_database_url](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic/env.py#L22-L29), [alembic.ini](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic.ini#L1-L4)

1) Alembic falls back to `sqlite:///./local.db`.
2) `alembic upgrade head` likely succeeds quickly (the current initial migration is largely SQLite-compatible).
   - Example migration: [20260601_0001_initial.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic/versions/20260601_0001_initial.py#L13-L44)
3) Uvicorn starts after migrations.

Conclusion:
- Absence of `DATABASE_URL` alone does not inherently crash startup in this repo; it falls back to SQLite.
- If Railway healthcheck is failing and there is no app startup output, this “SQLite fallback” scenario is less consistent with the symptoms (because Uvicorn would typically start).

### Case B: `DATABASE_URL` missing AND `POSTGRES_HOST` present
Source: [build_postgres_url_from_env](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/db/session.py#L38-L45)

1) Alembic attempts to build a Postgres URL from env vars.
2) `build_postgres_url_from_env()` requires `POSTGRES_PASSWORD`.
   - If `POSTGRES_PASSWORD` is missing/empty, it raises `RuntimeError`.
3) That exception causes `alembic upgrade head` to exit non-zero.
4) Because of `&&`, Uvicorn never starts.

Conclusion:
- A partial Postgres env setup (setting `POSTGRES_HOST` but not `POSTGRES_PASSWORD`) will hard-fail migrations and prevent startup.

## Does Startup Raise an Exception if `DATABASE_URL` Is Absent?

- Not by itself.
  - If neither `DATABASE_URL` nor `POSTGRES_HOST` are present, Alembic uses SQLite and proceeds.
- It can raise if `POSTGRES_HOST` is present but required companions (notably `POSTGRES_PASSWORD`) are missing.
  - This is an explicit `RuntimeError` from `_get_required_env("POSTGRES_PASSWORD")`.

## Does `alembic upgrade head` Exit Non-Zero?

Yes, if any of the following happen:
- Database URL resolution raises (e.g., `POSTGRES_PASSWORD` missing in Case B).
- Connection to the resolved DB URL fails or times out.
- Migration fails (DDL error, permissions, locking).

In those cases:
- `uvicorn ...` does not run at all due to `alembic upgrade head && uvicorn ...`.

## Exact Expected Railway Variable Name

Primary expected variable:
- `DATABASE_URL`

Supported (alternative) env set (primarily for local compose / custom setups):
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

Note:
- In this repo, `POSTGRES_PASSWORD` is required if using `POSTGRES_HOST` path.

## Probability Assessment (Given the Reported Symptoms)

Most consistent with “healthcheck fails” + “no application startup output”:

1) `alembic upgrade head` is blocking/failing before Uvicorn starts due to DB connectivity or migration failure while `DATABASE_URL` is present — High
2) `POSTGRES_HOST` is set (or injected) without `POSTGRES_PASSWORD`, causing an immediate `RuntimeError` before Uvicorn starts — Medium
3) `DATABASE_URL` is missing and Alembic uses SQLite, but Uvicorn still fails to start for another reason (import error, crash loop) — Low
4) `DATABASE_URL` missing causes startup exception directly — Very low (not true in Case A; only true in Case B with `POSTGRES_HOST`)

## Operational Implication for Railway Healthchecks

Because migrations run before the web server process:
- The service cannot pass HTTP healthchecks until migrations complete successfully.
- If the DB is not reachable immediately (or migrations are slow / blocked), Railway will see repeated failures on `/health` even though the container is “running”.
