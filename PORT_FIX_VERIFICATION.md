# RAILWAY_PORT_FIX_VERIFICATION

Repository root (actual `.git` root): `C:\workspace_lilith_public\_tmp_target\Lilith-Architecture`

Verified commit:
- HEAD: `5f6f91433f28059c5f4de37220b26d9da2ff34ff` (`main`, `origin/main`)
- Working tree: clean

## 1) CURRENT committed Dockerfile (from HEAD)

Source: `git show HEAD:Dockerfile`

### 2) Exact final CMD line

```
CMD ["sh", "-c", "alembic upgrade head && uvicorn lilith_replay_core.api.app:app --host ${API_HOST:-0.0.0.0} --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --no-access-log"]
```

### 3) Exact HEALTHCHECK line

```
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import json,os,urllib.request; port=os.environ.get('PORT') or os.environ.get('API_PORT') or '8000'; url=f'http://localhost:{port}/health'; print(json.loads(urllib.request.urlopen(url, timeout=2).read().decode('utf-8'))['ok'])"
```

## 4) Search Results

Search terms:
- `API_PORT:-8000`
- `PORT:-8000`
- `uvicorn`

Hits (not exhaustive, key locations):
- `PORT:-8000`
  - `Dockerfile: CMD ... --port ${PORT:-8000}`
- `API_PORT:-8000`
  - `docker-compose.yml: ... --port ${API_PORT:-8000}` (local compose, not the Dockerfile CMD)
- `uvicorn`
  - `Dockerfile`, `docker-compose.yml`, `Makefile`, docs, and logging config

## 5) Determination: does HEAD already contain the Railway port fix?

The required fix is: bind Uvicorn to Railway’s injected `PORT` (with fallback), and ensure health probing prefers `PORT`.

Evidence in HEAD:
- Uvicorn bind port uses `--port ${PORT:-8000}` in the Dockerfile CMD.
- Docker HEALTHCHECK selects port in this precedence order:
  1) `PORT`
  2) `API_PORT`
  3) `"8000"` fallback

Final conclusion:

PORT_FIX_PRESENT_IN_HEAD = YES
