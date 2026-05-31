from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import UUID4, BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from lilith_replay_core.db.runtime import get_sessionmaker, resolve_database_url
from lilith_replay_core.logging import get_logger, get_request_id, set_replay_run_id
from lilith_replay_core.persistence import create_replay_run, get_replay_run

router = APIRouter(prefix="/replay", tags=["replay"])
logger = get_logger(__name__)


class ArtifactCreate(BaseModel):
    artifact_type: str = Field(min_length=1, max_length=64)
    artifact_hash: str = Field(min_length=1, max_length=128)


class ReplayRunCreateRequest(BaseModel):
    run_id: UUID4 | None = Field(default=None)
    replay_type: str = Field(min_length=1, max_length=64)
    manifest_hash: str = Field(min_length=1, max_length=128)
    artifacts: list[ArtifactCreate] = Field(default_factory=list)


class ReplayRunCreateResponse(BaseModel):
    run_id: UUID4
    status: str = Field(default="created")


class ReplayRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: UUID4
    created_at: datetime
    replay_type: str
    status: str
    manifest_hash: str
    request_id: str


@router.post("/run", response_model=ReplayRunCreateResponse)
def create_run(payload: ReplayRunCreateRequest) -> ReplayRunCreateResponse:
    run_id = payload.run_id if payload.run_id is not None else uuid.uuid4()
    set_replay_run_id(str(run_id))
    request_id = get_request_id() or uuid.uuid4().hex

    sessionmaker_ = get_sessionmaker(resolve_database_url())
    try:
        persisted_run_id = create_replay_run(
            sessionmaker_,
            run_id=run_id,
            replay_type=payload.replay_type,
            manifest_hash=payload.manifest_hash,
            request_id=request_id,
            artifacts=[(a.artifact_type, a.artifact_hash) for a in payload.artifacts],
        )
    except IntegrityError as exc:
        logger.warning(
            "replay run persistence failed",
            extra={
                "event": "replay.create.fail",
                "data": {"replay_run_id": str(run_id), "error_type": type(exc).__name__},
            },
        )
        raise HTTPException(status_code=409, detail="replay_run_conflict") from exc

    logger.info(
        "replay run created",
        extra={
            "event": "replay.create.ok",
            "data": {"replay_run_id": str(persisted_run_id), "artifact_count": len(payload.artifacts)},
        },
    )
    return ReplayRunCreateResponse(run_id=persisted_run_id)


@router.get("/run/{run_id}", response_model=ReplayRunResponse)
def get_run(run_id: UUID4) -> ReplayRunResponse:
    set_replay_run_id(str(run_id))
    sessionmaker_ = get_sessionmaker(resolve_database_url())
    run = get_replay_run(sessionmaker_, run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="replay_run_not_found")
    return ReplayRunResponse.model_validate(run)
