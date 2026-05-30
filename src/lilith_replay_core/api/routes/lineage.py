from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from lilith_replay_core.lineage import LineageRecord
from lilith_replay_core.logging import get_logger, set_replay_run_id

router = APIRouter(prefix="/lineage", tags=["lineage"])
logger = get_logger(__name__)


class LineageResponse(BaseModel):
    ok: bool = Field(default=True)
    record: LineageRecord


@router.get("/{run_id}", response_model=LineageResponse)
def get_lineage(run_id: str) -> LineageResponse:
    set_replay_run_id(run_id)
    logger.info("lineage request", extra={"event": "lineage.request", "data": {"replay_run_id": run_id}})
    record = LineageRecord(run_id=run_id, created_at=datetime(1970, 1, 1, tzinfo=UTC), parents=[])
    return LineageResponse(record=record)
