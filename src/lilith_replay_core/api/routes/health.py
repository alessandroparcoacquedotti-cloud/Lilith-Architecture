from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from lilith_replay_core import __version__
from lilith_replay_core.health import db_check, import_check
from lilith_replay_core.logging import get_logger
from lilith_replay_core.observability import DB_CONNECTIVITY_CHECKS_TOTAL, counter_inc

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


class HealthResponse(BaseModel):
    ok: bool
    service: str = Field(default="lilith-replay-core")
    version: str = Field(default=__version__)


class HealthDbResponse(BaseModel):
    ok: bool
    configured: bool
    status: Literal["PASS", "SKIP", "FAIL"]
    error: Literal["db_not_configured", "db_extras_missing", "db_unreachable", "none"] = "none"


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    import_check()
    logger.info("health ok", extra={"event": "health.check"})
    return HealthResponse(ok=True)


@router.get("/health/db", response_model=HealthDbResponse)
def get_health_db() -> HealthDbResponse:
    configured = bool(os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_HOST"))
    if not configured:
        counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="skip")
        logger.info("db check skipped", extra={"event": "health.db_check", "data": {"result": "skip"}})
        return HealthDbResponse(ok=False, configured=False, status="SKIP", error="db_not_configured")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        from lilith_replay_core.db.session import build_postgres_url_from_env

        database_url = build_postgres_url_from_env()

    try:
        db_check(database_url)
        counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="pass")
        logger.info("db check pass", extra={"event": "health.db_check", "data": {"result": "pass"}})
        return HealthDbResponse(ok=True, configured=True, status="PASS", error="none")
    except RuntimeError:
        counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="fail")
        logger.warning(
            "db check fail",
            extra={"event": "health.db_check", "data": {"result": "fail", "error": "db_extras_missing"}},
        )
        return HealthDbResponse(ok=False, configured=True, status="FAIL", error="db_extras_missing")
    except Exception:
        counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="fail")
        logger.warning(
            "db check fail",
            extra={"event": "health.db_check", "data": {"result": "fail", "error": "db_unreachable"}},
        )
        return HealthDbResponse(ok=False, configured=True, status="FAIL", error="db_unreachable")
