from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReplayTelemetryRecord(BaseModel):
    kind: Literal["replay"] = "replay"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    request_id: str | None = None
    replay_run_id: str | None = None
    endpoint: str
    ok: bool
    duration_ms: float | None = None


class ValidationTelemetryRecord(BaseModel):
    kind: Literal["validation"] = "validation"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    request_id: str | None = None
    replay_run_id: str | None = None
    endpoint: str
    ok: bool
    error_count: int = 0
    warning_count: int = 0
    duration_ms: float | None = None


class DiffTelemetryRecord(BaseModel):
    kind: Literal["diff"] = "diff"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    request_id: str | None = None
    replay_run_id: str | None = None
    endpoint: str
    ok: bool
    schema_drift_detected: bool = False
    format: Literal["json", "csv"]
    duration_ms: float | None = None

