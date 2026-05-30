from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReplayManifest(BaseModel):
    run_id: str = Field(..., description="Stable identifier for the replay run.")
    replay_timestamp: datetime = Field(..., description="UTC timestamp associated with the replay.")
    fixtures_processed: int = Field(..., ge=0, description="Count of fixtures processed in the replay.")
    audit_schema_version: str = Field(..., description="Version of the public audit schema.")
    integrity_hash: str = Field(..., description="Integrity hash covering replay artifacts.")
