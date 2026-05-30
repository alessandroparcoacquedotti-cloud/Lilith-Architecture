from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class LineageRecord(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime(1970, 1, 1, tzinfo=UTC))
    parents: list[str] = Field(default_factory=list)
