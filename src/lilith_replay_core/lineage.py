from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LineageArtifact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    artifact_id: int
    artifact_type: str
    artifact_hash: str
    created_at: datetime


class LineageRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    created_at: datetime
    replay_type: str
    status: str
    manifest_hash: str
    request_id: str
    artifacts: list[LineageArtifact] = Field(default_factory=list)
