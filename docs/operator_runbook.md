# Operator Runbook (Public-Safe)

This runbook focuses on verifiable checks you can perform against a running deployment (local or hosted) without requiring privileged access or internal tooling.

## Base URL

Set a base URL for commands below:

- Local: `http://localhost:8000`
- Deployed: `https://<railway-public-domain>`

## Deployment Verification

Confirm the service is reachable and serving HTTP:

```bash
curl -i $BASE_URL/health
```

Expected:

- HTTP 200
- JSON body includes `{"ok": true, "service": "lilith-replay-core", "version": "..."}`
- Response header contains `X-Request-ID`

## Health Verification

Basic health:

```bash
curl -s $BASE_URL/health | python -m json.tool
```

## Database Verification

Database health endpoint:

```bash
curl -s $BASE_URL/health/db | python -m json.tool
```

Expected outcomes:

- If no DB is configured: `configured=false`, `status="SKIP"`, `error="db_not_configured"`, HTTP 200
- If DB is configured but DB extras are missing: `status="FAIL"`, `error="db_extras_missing"`, HTTP 200
- If DB is configured and reachable: `ok=true`, `status="PASS"`, HTTP 200

Operational notes:

- This endpoint is designed to be safe for public exposure: it returns structured status without leaking connection strings.

## Metrics Verification

Prometheus exposition endpoint:

```bash
curl -s $BASE_URL/metrics | head -n 40
```

Expected:

- HTTP 200
- Text format includes metric families such as:
  - `api_requests_total`
  - `api_request_duration_seconds`
  - `api_startups_total`
  - `replay_validation_requests_total`
  - `deterministic_diff_requests_total`

If `/metrics` returns 404:

- Metrics are disabled (`ENABLE_METRICS=0`), or the server was started with metrics disabled.

## Swagger/OpenAPI Verification

Swagger UI:

```bash
curl -i $BASE_URL/docs
```

OpenAPI schema:

```bash
curl -s $BASE_URL/openapi.json | python -m json.tool | head -n 40
```

Expected:

- `/docs` returns HTML
- `/openapi.json` returns JSON and includes `info.title`
