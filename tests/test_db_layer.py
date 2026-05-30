from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from lilith_replay_core.api.app import app
from lilith_replay_core.db.base import Base
from lilith_replay_core.db.models import ArtifactRecord, ReplayRun, ReplayRunStatus
from lilith_replay_core.db.session import create_engine, create_sessionmaker, session_scope


def _repo_head_revision() -> str:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    repo_root = Path(__file__).resolve().parents[1]
    cfg = Config()
    cfg.set_main_option("script_location", str(repo_root / "alembic"))
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    assert head
    return head


def test_models_can_persist_and_query_sqlite(tmp_path) -> None:
    db_path = tmp_path / "db.sqlite"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)

    maker = create_sessionmaker(engine)
    with session_scope(maker) as session:
        run = ReplayRun(
            run_id="run-1",
            replay_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            status=ReplayRunStatus.PENDING,
            fixtures_processed=3,
        )
        session.add(run)
        session.flush()

        artifact = ArtifactRecord(
            run_id="run-1",
            artifact_type="manifest",
            artifact_path="examples/replay_manifest_valid.json",
            integrity_hash="abc",
        )
        session.add(artifact)

    with session_scope(maker) as session:
        fetched = session.query(ReplayRun).filter_by(run_id="run-1").one()
        assert fetched.fixtures_processed == 3
        assert fetched.status == ReplayRunStatus.PENDING

        artifacts = session.query(ArtifactRecord).filter_by(run_id="run-1").all()
        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == "manifest"


def test_session_scope_rolls_back_on_error(tmp_path) -> None:
    db_path = tmp_path / "db.sqlite"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    Base.metadata.create_all(engine)

    maker = create_sessionmaker(engine)
    try:
        with session_scope(maker) as session:
            session.add(
                ReplayRun(
                    run_id="run-dup",
                    replay_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                    status=ReplayRunStatus.PENDING,
                    fixtures_processed=0,
                )
            )
        with session_scope(maker) as session:
            session.add(
                ReplayRun(
                    run_id="run-dup",
                    replay_timestamp=datetime(2026, 1, 2, tzinfo=UTC),
                    status=ReplayRunStatus.PENDING,
                    fixtures_processed=0,
                )
            )
    except Exception:
        pass

    with session_scope(maker) as session:
        runs = session.query(ReplayRun).filter_by(run_id="run-dup").all()
        assert len(runs) == 1


def test_health_db_reports_unmigrated_when_alembic_version_missing(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "db.sqlite"
    url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)

    client = TestClient(app)
    resp = client.get("/health/db")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"] == "PASS"
    assert body["migration_status"] == "OUTDATED"
    assert body["database_revision"] is None
    assert body["repository_head_revision"] == _repo_head_revision()
    assert body["request_id"]


def test_health_db_reports_outdated_when_revision_differs(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "db.sqlite"
    url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": "000000000000"})
        conn.commit()

    monkeypatch.setenv("DATABASE_URL", url)

    client = TestClient(app)
    resp = client.get("/health/db")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"] == "PASS"
    assert body["migration_status"] == "OUTDATED"
    assert body["database_revision"] == "000000000000"
    assert body["repository_head_revision"] == _repo_head_revision()
    assert body["request_id"]


def test_health_db_reports_up_to_date_when_revision_matches(tmp_path, monkeypatch) -> None:
    head = _repo_head_revision()
    db_path = tmp_path / "db.sqlite"
    url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:v)"), {"v": head})
        conn.commit()

    monkeypatch.setenv("DATABASE_URL", url)

    client = TestClient(app)
    resp = client.get("/health/db")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"] == "PASS"
    assert body["migration_status"] == "UP_TO_DATE"
    assert body["database_revision"] == head
    assert body["repository_head_revision"] == head
    assert body["request_id"]
