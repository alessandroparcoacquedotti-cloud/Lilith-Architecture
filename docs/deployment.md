# Deployment (Public-Safe)

This service is designed to run as a container-first FastAPI backend with:

- `GET /health` for health checks
- `GET /metrics` for Prometheus metrics (when enabled)
- `GET /docs` for Swagger UI

## Environment Variables

- `APP_ENV`: Environment name (e.g. `development`, `production`). Default: `development`
- `LOG_LEVEL`: Application log level (e.g. `INFO`). Default: `INFO`
- `API_HOST`: Bind host used by the container entrypoint. Default: `0.0.0.0`
- `API_PORT`: Bind port used by the container entrypoint. Default: `8000`
- `ENABLE_METRICS`: Enable `/metrics` (`1`/`0`). Default: `1`
- `DATABASE_URL`: Optional database URL. Used by `/health/db` when present.

## Docker Deploy

```bash
docker build -t lilith-replay .
docker run --rm -p 8000:8000 -e APP_ENV=production -e LOG_LEVEL=INFO lilith-replay
```

Check:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/metrics`

## Railway Deploy

- Dockerfile deploy
- Health check path: `/health`

## Render Deploy

- Docker deploy using `render.yaml`
- Health check path: `/health`
