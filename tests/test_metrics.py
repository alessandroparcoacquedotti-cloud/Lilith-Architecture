from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

from lilith_replay_core.api.app import app
from lilith_replay_core.db.base import Base
from lilith_replay_core.db.session import create_engine


def _sample_value(metrics_text: str, name: str, labels: dict[str, str] | None = None) -> float | None:
    selected_labels = labels or {}
    for family in text_string_to_metric_families(metrics_text):
        for sample in family.samples:
            if sample.name != name:
                continue
            if all(sample.labels.get(k) == v for k, v in selected_labels.items()):
                return float(sample.value)
    return None


def test_metrics_endpoint_exposes_new_metrics(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "metrics.sqlite"
    url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)

    engine = create_engine(url)
    Base.metadata.create_all(engine)

    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text

    assert "replay_runs_created_total" in body
    assert "artifact_records_created_total" in body
    assert "lineage_requests_total" in body
    assert "db_transactions_total" in body
    assert "db_operation_duration_seconds" in body


def test_replay_and_lineage_metrics_increment_and_labels(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "metrics.sqlite"
    url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)

    engine = create_engine(url)
    Base.metadata.create_all(engine)

    client = TestClient(app)
    replay_type = f"t_{uuid.uuid4().hex[:16]}"
    artifact_type_a = f"a_{uuid.uuid4().hex[:16]}"
    artifact_type_b = f"b_{uuid.uuid4().hex[:16]}"
    payload = {
        "replay_type": replay_type,
        "manifest_hash": "manifest-hash-1",
        "artifacts": [
            {"artifact_type": artifact_type_a, "artifact_hash": "h1"},
            {"artifact_type": artifact_type_b, "artifact_hash": "h2"},
        ],
    }

    created = client.post("/api/v1/replay/run", json=payload)
    assert created.status_code == 200
    run_id = created.json()["run_id"]

    metrics_text = client.get("/metrics").text
    assert (
        _sample_value(
            metrics_text,
            "replay_runs_created_total",
            {"replay_type": replay_type, "status": "created"},
        )
        == 1.0
    )
    assert _sample_value(metrics_text, "artifact_records_created_total", {"artifact_type": artifact_type_a}) == 1.0
    assert _sample_value(metrics_text, "artifact_records_created_total", {"artifact_type": artifact_type_b}) == 1.0

    lineage_ok = client.get(f"/api/v1/lineage/{run_id}")
    assert lineage_ok.status_code == 200
    metrics_text = client.get("/metrics").text
    assert _sample_value(metrics_text, "lineage_requests_total", {"status": "success"}) is not None

    missing_id = str(uuid.uuid4())
    lineage_missing = client.get(f"/api/v1/lineage/{missing_id}")
    assert lineage_missing.status_code == 404
    metrics_text = client.get("/metrics").text
    assert _sample_value(metrics_text, "lineage_requests_total", {"status": "not_found"}) is not None


def test_db_transactions_failure_increments(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "metrics.sqlite"
    url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)

    engine = create_engine(url)
    Base.metadata.create_all(engine)

    client = TestClient(app)
    before = _sample_value(
        client.get("/metrics").text,
        "db_transactions_total",
        {"operation": "create_replay", "result": "failure"},
    )
    before_value = 0.0 if before is None else before

    run_id = str(uuid.uuid4())
    payload = {
        "run_id": run_id,
        "replay_type": "rollback_test",
        "manifest_hash": "manifest-hash-1",
        "artifacts": [
            {"artifact_type": "manifest", "artifact_hash": "dup"},
            {"artifact_type": "manifest", "artifact_hash": "dup"},
        ],
    }
    created = client.post("/api/v1/replay/run", json=payload)
    assert created.status_code == 409

    after = _sample_value(
        client.get("/metrics").text,
        "db_transactions_total",
        {"operation": "create_replay", "result": "failure"},
    )
    assert after is not None
    assert after == before_value + 1.0
