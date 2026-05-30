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

ARG INSTALL_EXTRAS="api"
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    if [ -n "$INSTALL_EXTRAS" ]; then python -m pip install ".[${INSTALL_EXTRAS}]"; else python -m pip install .; fi

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

USER app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import json,urllib.request; print(json.loads(urllib.request.urlopen('http://localhost:8000/health', timeout=2).read().decode('utf-8'))['ok'])"

CMD ["sh", "-c", "uvicorn lilith_replay_core.api.app:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --no-access-log"]
