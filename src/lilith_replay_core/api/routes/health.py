from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from lilith_replay_core import __version__
from lilith_replay_core.health import import_check
from lilith_replay_core.logging import get_logger, get_request_id
from lilith_replay_core.observability import DB_CONNECTIVITY_CHECKS_TOTAL, counter_inc

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


class HealthResponse(BaseModel):
    ok: bool
    service: str = Field(default="lilith-replay-core")
    version: str = Field(default=__version__)


class HealthDbGovernanceResponse(BaseModel):
    database: Literal["PASS", "FAIL"]
    migration_status: Literal["UP_TO_DATE", "OUTDATED", "UNKNOWN"]
    database_revision: str | None = None
    repository_head_revision: str | None = None
    request_id: str


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    import_check()
    logger.info("health ok", extra={"event": "health.check"})
    return HealthResponse(ok=True)


def _discover_repo_root() -> Path | None:
    cwd = Path.cwd()
    if (cwd / "alembic").exists():
        return cwd

    p = Path(__file__).resolve()
    for parent in p.parents:
        if parent.name == "src":
            return parent.parent
    return None


def _get_repository_head_revision(repo_root: Path) -> str | None:
    alembic_dir = repo_root / "alembic"
    if not alembic_dir.exists():
        return None

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
    except ModuleNotFoundError:
        return None

    cfg = Config()
    cfg.set_main_option("script_location", str(alembic_dir))
    script = ScriptDirectory.from_config(cfg)
    return script.get_current_head()


@router.get("/health/db", response_model=HealthDbGovernanceResponse)
def get_health_db() -> HealthDbGovernanceResponse:
    request_id = get_request_id() or ""
    configured = bool(os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_HOST"))
    if not configured:
        counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="fail")
        logger.info("db check skipped", extra={"event": "health.db_check", "data": {"result": "skip"}})
        return HealthDbGovernanceResponse(
            database="FAIL",
            migration_status="UNKNOWN",
            database_revision=None,
            repository_head_revision=None,
            request_id=request_id,
        )

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        try:
            from lilith_replay_core.db.session import build_postgres_url_from_env

            database_url = build_postgres_url_from_env()
        except RuntimeError:
            counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="fail")
            logger.warning("db check fail", extra={"event": "health.db_check", "data": {"result": "fail"}})
            return HealthDbGovernanceResponse(
                database="FAIL",
                migration_status="UNKNOWN",
                database_revision=None,
                repository_head_revision=None,
                request_id=request_id,
            )

    try:
        from sqlalchemy import text

        from lilith_replay_core.db.session import create_engine

        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            try:
                from alembic.runtime.migration import MigrationContext
            except ModuleNotFoundError:
                counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="fail")
                logger.warning("db check fail", extra={"event": "health.db_check", "data": {"result": "fail"}})
                return HealthDbGovernanceResponse(
                    database="FAIL",
                    migration_status="UNKNOWN",
                    database_revision=None,
                    repository_head_revision=None,
                    request_id=request_id,
                )
            db_ctx = MigrationContext.configure(conn)
            database_revision = db_ctx.get_current_revision()

        repo_root = _discover_repo_root()
        repository_head_revision = _get_repository_head_revision(repo_root) if repo_root else None

        if repository_head_revision is None:
            migration_status: Literal["UP_TO_DATE", "OUTDATED", "UNKNOWN"] = "UNKNOWN"
        elif database_revision is None:
            migration_status = "OUTDATED"
        elif database_revision == repository_head_revision:
            migration_status = "UP_TO_DATE"
        else:
            migration_status = "OUTDATED"

        counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="pass")
        logger.info("db check pass", extra={"event": "health.db_check", "data": {"result": "pass"}})
        return HealthDbGovernanceResponse(
            database="PASS",
            migration_status=migration_status,
            database_revision=database_revision,
            repository_head_revision=repository_head_revision,
            request_id=request_id,
        )
    except ModuleNotFoundError:
        counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="fail")
        logger.warning(
            "db check fail",
            extra={"event": "health.db_check", "data": {"result": "fail", "error": "db_extras_missing"}},
        )
        return HealthDbGovernanceResponse(
            database="FAIL",
            migration_status="UNKNOWN",
            database_revision=None,
            repository_head_revision=None,
            request_id=request_id,
        )
    except Exception:
        counter_inc(DB_CONNECTIVITY_CHECKS_TOTAL, result="fail")
        logger.warning(
            "db check fail",
            extra={"event": "health.db_check", "data": {"result": "fail", "error": "db_unreachable"}},
        )
        return HealthDbGovernanceResponse(
            database="FAIL",
            migration_status="UNKNOWN",
            database_revision=None,
            repository_head_revision=None,
            request_id=request_id,
        )
