# Contributing

Thanks for your interest in contributing. This repository is intentionally scoped as a public-safe backend for deterministic replay validation, governance/audit primitives, and observability.

## Ground Rules

- Do not add prediction logic, betting logic, private datasets, secrets, operational thresholds, or production internals.
- Do not commit `.env` files or credential-bearing configs.
- Keep changes deterministic and auditable. Prefer stable outputs and low-cardinality telemetry.

## Development Setup

### Python setup (API + DB + dev tooling)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev,db,api]"
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
& .\.venv\Scripts\python.exe -m pip install -U pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev,db,api]"
```

### Run the API locally

```bash
uvicorn lilith_replay_core.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Verify:

- `http://localhost:8000/docs`
- `http://localhost:8000/health`
- `http://localhost:8000/metrics`

### Run with Docker Compose (API + Postgres)

```bash
docker compose up --build
```

### Run checks

```bash
ruff check src tests scripts_public
mypy src
pytest
```

Makefile shortcuts (optional):

```bash
make lint
make typecheck
make test
```

## Pull Request Checklist

- Tests pass (`pytest`)
- Lint passes (`ruff check`)
- Types pass (`mypy src`)
- Public-safe posture preserved (no secrets, no sensitive artifacts, no internal logic leakage)
- Logs remain structured JSON and do not include request bodies or artifacts
- Metrics avoid user-derived labels and high-cardinality dimensions

## Security Reports

For vulnerability reporting, follow [SECURITY.md](SECURITY.md).
