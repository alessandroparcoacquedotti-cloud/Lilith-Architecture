from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from sqlalchemy import select

from lilith_replay_core.db.models import ArtifactRecord, ReplayRun, ReplayRunStatus
from lilith_replay_core.db.session import SessionMaker, session_scope
from lilith_replay_core.observability import (
    ARTIFACT_RECORDS_CREATED_TOTAL,
    DB_OPERATION_DURATION_SECONDS,
    DB_TRANSACTIONS_TOTAL,
    REPLAY_RUNS_CREATED_TOTAL,
    counter_inc,
    hist_observe,
)


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
    start = time.perf_counter()
    try:
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
        duration_s = time.perf_counter() - start
        counter_inc(DB_TRANSACTIONS_TOTAL, operation="create_replay", result="success")
        hist_observe(DB_OPERATION_DURATION_SECONDS, duration_s, operation="create_replay")
        counter_inc(
            REPLAY_RUNS_CREATED_TOTAL,
            replay_type=replay_type,
            status=ReplayRunStatus.CREATED.value,
        )
        for artifact_type, _artifact_hash in artifacts:
            counter_inc(ARTIFACT_RECORDS_CREATED_TOTAL, artifact_type=artifact_type)
        return run_id
    except Exception:
        duration_s = time.perf_counter() - start
        counter_inc(DB_TRANSACTIONS_TOTAL, operation="create_replay", result="failure")
        hist_observe(DB_OPERATION_DURATION_SECONDS, duration_s, operation="create_replay")
        raise


def get_replay_run(sessionmaker_: SessionMaker, *, run_id: uuid.UUID) -> ReplayRun | None:
    start = time.perf_counter()
    try:
        with session_scope(sessionmaker_) as session:
            run = session.get(ReplayRun, run_id)
        duration_s = time.perf_counter() - start
        counter_inc(DB_TRANSACTIONS_TOTAL, operation="read_replay", result="success")
        hist_observe(DB_OPERATION_DURATION_SECONDS, duration_s, operation="read_replay")
        return run
    except Exception:
        duration_s = time.perf_counter() - start
        counter_inc(DB_TRANSACTIONS_TOTAL, operation="read_replay", result="failure")
        hist_observe(DB_OPERATION_DURATION_SECONDS, duration_s, operation="read_replay")
        raise


def get_lineage(sessionmaker_: SessionMaker, *, run_id: uuid.UUID) -> LineageData | None:
    start = time.perf_counter()
    try:
        with session_scope(sessionmaker_) as session:
            run = session.get(ReplayRun, run_id)
            if run is None:
                lineage = None
            else:
                artifacts = list(
                    session.scalars(
                        select(ArtifactRecord)
                        .where(ArtifactRecord.run_id == run_id)
                        .order_by(ArtifactRecord.created_at.asc(), ArtifactRecord.artifact_id.asc())
                    )
                )
                lineage = LineageData(run=run, artifacts=artifacts)
        duration_s = time.perf_counter() - start
        counter_inc(DB_TRANSACTIONS_TOTAL, operation="read_lineage", result="success")
        hist_observe(DB_OPERATION_DURATION_SECONDS, duration_s, operation="read_lineage")
        return lineage
    except Exception:
        duration_s = time.perf_counter() - start
        counter_inc(DB_TRANSACTIONS_TOTAL, operation="read_lineage", result="failure")
        hist_observe(DB_OPERATION_DURATION_SECONDS, duration_s, operation="read_lineage")
        raise
