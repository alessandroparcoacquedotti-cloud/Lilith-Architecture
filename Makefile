.PHONY: install test lint lint-fix typecheck api docker-build docker-up

install:
	python -m pip install -U pip
	python -m pip install -e ".[dev,db,api]"

test:
	python -m pytest

lint:
	python -m ruff check src tests scripts_public

lint-fix:
	python -m ruff check --fix src tests scripts_public

typecheck:
	python -m mypy src

api:
	uvicorn lilith_replay_core.api.app:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t lilith-replay-core:dev --build-arg INSTALL_EXTRAS=db,api .

docker-up:
	docker compose up --build
