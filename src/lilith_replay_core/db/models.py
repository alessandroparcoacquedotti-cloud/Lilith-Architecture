from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lilith_replay_core.db.base import Base


class ReplayRunStatus(enum.StrEnum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class ReplayRun(Base):
    __tablename__ = "replay_runs"

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    replay_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[ReplayRunStatus] = mapped_column(
        SAEnum(ReplayRunStatus, name="replay_run_status"),
        nullable=False,
        default=ReplayRunStatus.CREATED,
        index=True,
    )
    manifest_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    artifacts: Mapped[list[ArtifactRecord]] = relationship(back_populates="replay_run")


class ArtifactRecord(Base):
    __tablename__ = "artifact_records"
    __table_args__ = (UniqueConstraint("run_id", "artifact_type", "artifact_hash"),)

    artifact_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("replay_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    artifact_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    replay_run: Mapped[ReplayRun] = relationship(back_populates="artifacts")
