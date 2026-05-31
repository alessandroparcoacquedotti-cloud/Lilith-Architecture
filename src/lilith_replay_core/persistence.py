from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select

from lilith_replay_core.db.models import ArtifactRecord, ReplayRun, ReplayRunStatus
from lilith_replay_core.db.session import SessionMaker, session_scope


@dataclass(frozen=True, slots=True)
class LineageData:
    run: ReplayRun
    artifacts: list[ArtifactRecord]


def create_replay_run(
    sessionmaker_: SessionMaker,
    *,
    run_id: uuid.UUID,
    replay_type: str,
    manifest_hash: str,
    request_id: str,
    artifacts: list[tuple[str, str]],
) -> uuid.UUID:
    with session_scope(sessionmaker_) as session:
        run = ReplayRun(
            run_id=run_id,
            replay_type=replay_type,
            status=ReplayRunStatus.CREATED,
            manifest_hash=manifest_hash,
            request_id=request_id,
        )
        session.add(run)
        for artifact_type, artifact_hash in artifacts:
            session.add(
                ArtifactRecord(
                    run_id=run_id,
                    artifact_type=artifact_type,
                    artifact_hash=artifact_hash,
                )
            )
        session.flush()
        return run.run_id


def get_replay_run(sessionmaker_: SessionMaker, *, run_id: uuid.UUID) -> ReplayRun | None:
    with session_scope(sessionmaker_) as session:
        return session.get(ReplayRun, run_id)


def get_lineage(sessionmaker_: SessionMaker, *, run_id: uuid.UUID) -> LineageData | None:
    with session_scope(sessionmaker_) as session:
        run = session.get(ReplayRun, run_id)
        if run is None:
            return None
        artifacts = list(
            session.scalars(
                select(ArtifactRecord)
                .where(ArtifactRecord.run_id == run_id)
                .order_by(ArtifactRecord.created_at.asc(), ArtifactRecord.artifact_id.asc())
            )
        )
        return LineageData(run=run, artifacts=artifacts)
