# Development

## Local setup

Create and activate a virtual environment (Python 3.11+), then install in editable mode:

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

## Run checks

```bash
ruff check src tests scripts_public
mypy src
pytest
```

## Local API

```bash
uvicorn lilith_replay_core.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Environment variables (optional):

- `APP_ENV` (default `development`)
- `LOG_LEVEL` (default `INFO`)
- `ENABLE_METRICS` (default enabled)
- `DATABASE_URL` (optional; used by `/health/db`)
