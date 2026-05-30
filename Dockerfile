FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

ARG INSTALL_EXTRAS="db,api"
RUN python -m pip install --upgrade pip && \
    if [ -n "$INSTALL_EXTRAS" ]; then python -m pip install ".[${INSTALL_EXTRAS}]"; else python -m pip install .; fi

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

USER app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import json,os,urllib.request; port=os.environ.get('PORT') or os.environ.get('API_PORT') or '8000'; url=f'http://localhost:{port}/health'; print(json.loads(urllib.request.urlopen(url, timeout=2).read().decode('utf-8'))['ok'])"

CMD ["sh", "-c", "alembic upgrade head && uvicorn lilith_replay_core.api.app:app --host ${API_HOST:-0.0.0.0} --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --no-access-log"]
