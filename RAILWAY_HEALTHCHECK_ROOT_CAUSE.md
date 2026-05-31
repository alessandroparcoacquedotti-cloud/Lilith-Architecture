# RAILWAY_HEALTHCHECK_ROOT_CAUSE_AUDIT

Repository: `C:\workspace_lilith_public\_tmp_target\Lilith-Architecture`

Context:
- Build succeeds
- PostgreSQL service exists
- `DATABASE_URL` exists on the Railway Postgres service
- Railway healthcheck never succeeds; Railway reports `SERVICE UNAVAILABLE`
- Previous logs showed `sqlite3.OperationalError`
- `PORT` fix is already present in HEAD

## 1) Current Implementation (Inspected)

### `/health` endpoint
Source: [health route](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/api/routes/health.py#L33-L38)

`GET /health`:
- runs `import_check()` and returns HTTP 200 with `{"ok": true, ...}`
- does not touch the database

Conclusion:
- `/health` does not require a working database connection.

### `db/session.py`
Source: [session.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/db/session.py#L15-L49)

Key points:
- `normalize_database_url()` rewrites `postgres://` and `postgresql://` to `postgresql+psycopg://`.
- `build_postgres_url_from_env()` raises `RuntimeError` if `POSTGRES_PASSWORD` is missing/empty.

### `alembic/env.py`
Source: [env.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic/env.py#L22-L29)

DB URL selection order used by Alembic at startup:
1) `DATABASE_URL` (normalized)
2) if `POSTGRES_HOST` exists: build from `POSTGRES_*` env
3) fall back to `alembic.ini` `sqlalchemy.url`

The fallback is SQLite:
- `sqlalchemy.url = sqlite:///./local.db` ([alembic.ini](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic.ini#L1-L4))

### Dockerfile startup command
Source: [Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L40-L42)

Startup is a strict chain:

```sh
alembic upgrade head && uvicorn ...
```

Implications:
- Startup can fail before Uvicorn starts (and then `/health` is unreachable).
- If `alembic upgrade head` exits non-zero, Uvicorn never starts.

## 2) Determinations (Requested)

### Does `/health` require a working DB connection?
- No.
  - It only calls `import_check()` ([health route](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/api/routes/health.py#L33-L38)).

### Can startup fail before Uvicorn starts?
- Yes.
  - Because `alembic upgrade head` runs first and is chained with `&&` ([Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L42)).

### Can `alembic upgrade head` terminate the container “silently”?
- It can terminate the container before any FastAPI/Uvicorn startup logs appear.
  - If Alembic fails, Uvicorn never starts, so you will not see application startup output.
  - Alembic still emits logs/errors to stderr, but operationally this often looks like “no app output” because the server process never comes up.

## 3) Most Likely Root Cause (Ranked 1–5)

### 1) Web service is not receiving `DATABASE_URL`, so Alembic falls back to SQLite and fails (matches `sqlite3.OperationalError`)
- Confidence: 85%
- Evidence:
  - Alembic falls back to SQLite when `DATABASE_URL` is missing in the running container ([env.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic/env.py#L22-L29), [alembic.ini](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic.ini#L1-L4)).
  - The Dockerfile runs migrations before Uvicorn; any Alembic failure prevents the web server from starting ([Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L42)).
  - Reported historical error is `sqlite3.OperationalError`, which is consistent with the SQLite fallback path being taken in production.
- Exact code locations:
  - Alembic fallback to SQLite: [env.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic/env.py#L22-L29) + [alembic.ini](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic.ini#L1-L4)
  - “migrations gate startup”: [Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L42)
- Minimal fix required (no code):
  - Ensure the Railway web service has `DATABASE_URL` in its own runtime environment (not only on the Postgres service).
  - In Railway terms: expose/reference the Postgres service `DATABASE_URL` into the web service’s variables so the container sees it at runtime.

### 2) Partial Postgres env present (e.g. `POSTGRES_HOST` set) but `POSTGRES_PASSWORD` missing, causing Alembic to raise and exit
- Confidence: 50%
- Evidence:
  - If `POSTGRES_HOST` is present and `DATABASE_URL` is absent, Alembic calls `build_postgres_url_from_env()`, which raises if `POSTGRES_PASSWORD` is missing ([session.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/db/session.py#L28-L45), [env.py](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/alembic/env.py#L22-L29)).
  - This would prevent Uvicorn from starting due to `&&` ([Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L42)).
- Minimal fix required (no code):
  - Either provide a valid `DATABASE_URL` to the web service, or ensure the full set of required `POSTGRES_*` vars is present (especially `POSTGRES_PASSWORD`).

### 3) `DATABASE_URL` is present but points to an unreachable DB at container start (network/DNS/ACL) or requires time to become ready, so Alembic blocks/fails and Uvicorn never starts
- Confidence: 45%
- Evidence:
  - Migrations run synchronously before the server starts ([Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L42)).
  - Any connection failure or timeout in Alembic prevents startup.
- Minimal fix required (no code):
  - Confirm the web service can reach the Postgres host/port specified by `DATABASE_URL` at runtime (same Railway project/network, correct internal hostname, correct firewall settings).

### 4) Migration failure due to permissions/locking/concurrency (e.g., multiple replicas running `alembic upgrade head` simultaneously)
- Confidence: 25%
- Evidence:
  - Startup runs `alembic upgrade head` unconditionally; in multi-replica scenarios migrations can contend.
  - A failing migration prevents Uvicorn from starting ([Dockerfile](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/Dockerfile#L42)).
- Minimal fix required (no code):
  - Deploy with a single replica during migrations; scale only after migration completes.
  - Ensure the Postgres user in `DATABASE_URL` has schema/table creation privileges.

### 5) `/health` itself returns non-200 due to DB unavailability
- Confidence: 5%
- Evidence:
  - `/health` does not query DB; it only imports modules and returns 200 ([health route](file:///c:/workspace_lilith_public/_tmp_target/Lilith-Architecture/src/lilith_replay_core/api/routes/health.py#L33-L38)).
- Minimal fix required:
  - None; this is not consistent with the current code.

## Final Takeaway

Given:
- `PORT` fix is already present,
- Railway returns `SERVICE UNAVAILABLE` (consistent with “no server listening”), and
- prior `sqlite3.OperationalError`,

the most likely explanation is that the runtime container does not see `DATABASE_URL`, Alembic falls back to SQLite (`sqlite:///./local.db`), Alembic fails, and Uvicorn never starts.
