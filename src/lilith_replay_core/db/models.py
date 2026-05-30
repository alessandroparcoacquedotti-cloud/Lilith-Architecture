from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lilith_replay_core.db.base import Base


class ReplayRunStatus(enum.StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ReplayRun(Base):
    __tablename__ = "replay_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    replay_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    status: Mapped[ReplayRunStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ReplayRunStatus.PENDING.value,
        index=True,
    )
    fixtures_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    artifacts: Mapped[list[ArtifactRecord]] = relationship(back_populates="replay_run")


class ArtifactRecord(Base):
    __tablename__ = "artifact_records"
    __table_args__ = (UniqueConstraint("run_id", "artifact_type", "artifact_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("replay_runs.run_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)
    integrity_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    replay_run: Mapped[ReplayRun] = relationship(back_populates="artifacts")
