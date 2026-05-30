from __future__ import annotations

import os

from pydantic import BaseModel, Field


class PublicReplayConfig(BaseModel):
    replay_timezone: str = Field(default="UTC")
    audit_schema_version: str = Field(default="1")


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    s = value.strip().lower()
    if s in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _parse_int(value: str | None, *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value.strip())
    except Exception:
        return default


class AppSettings(BaseModel):
    app_env: str = Field(default="development", description="Runtime environment name (development|production).")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG|INFO|WARNING|ERROR).")
    api_host: str = Field(default="0.0.0.0", description="Bind host for the API server.")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Bind port for the API server.")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus /metrics endpoint.")
    database_url: str | None = Field(default=None, description="Database URL (optional).")


def load_settings(environ: dict[str, str] | None = None) -> AppSettings:
    env = os.environ if environ is None else environ
    return AppSettings(
        app_env=(env.get("APP_ENV") or "development").strip() or "development",
        log_level=(env.get("LOG_LEVEL") or "INFO").strip() or "INFO",
        api_host=(env.get("API_HOST") or "0.0.0.0").strip() or "0.0.0.0",
        api_port=_parse_int(env.get("API_PORT"), default=8000),
        enable_metrics=_parse_bool(env.get("ENABLE_METRICS"), default=True),
        database_url=(env.get("DATABASE_URL") or None),
    )
