from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import UUID4, BaseModel, Field

from lilith_replay_core.db.runtime import get_sessionmaker, resolve_database_url
from lilith_replay_core.lineage import LineageRecord
from lilith_replay_core.logging import get_logger, set_replay_run_id
from lilith_replay_core.persistence import get_lineage

router = APIRouter(prefix="/lineage", tags=["lineage"])
logger = get_logger(__name__)


class LineageResponse(BaseModel):
    ok: bool = Field(default=True)
    record: LineageRecord


@router.get("/{run_id}", response_model=LineageResponse)
def get_lineage_route(run_id: UUID4) -> LineageResponse:
    set_replay_run_id(str(run_id))
    logger.info("lineage request", extra={"event": "lineage.request", "data": {"replay_run_id": str(run_id)}})

    sessionmaker_ = get_sessionmaker(resolve_database_url())
    data = get_lineage(sessionmaker_, run_id=run_id)
    if data is None:
        raise HTTPException(status_code=404, detail="lineage_not_found")

    record = LineageRecord.model_validate(
        {
            "run_id": data.run.run_id,
            "created_at": data.run.created_at,
            "replay_type": data.run.replay_type,
            "status": data.run.status,
            "manifest_hash": data.run.manifest_hash,
            "request_id": data.run.request_id,
            "artifacts": data.artifacts,
        }
    )
    return LineageResponse(record=record)
