from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from lilith_replay_core.api.app import app, create_app
from lilith_replay_core.config import AppSettings
from lilith_replay_core.db.base import Base
from lilith_replay_core.db.session import create_engine
from lilith_replay_core.logging import JsonFormatter, set_replay_run_id, set_request_id


def test_health_ok() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert resp.headers.get("X-Request-ID")


def test_request_id_propagates_when_provided() -> None:
    client = TestClient(app)
    resp = client.get("/health", headers={"X-Request-ID": "req-test-123"})
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == "req-test-123"


def test_health_db_skips_when_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_HOST", raising=False)

    client = TestClient(app)
    resp = client.get("/health/db")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"] == "FAIL"
    assert body["migration_status"] == "UNKNOWN"
    assert body["database_revision"] is None
    assert body["repository_head_revision"] is None
    assert body["request_id"]


def test_manifest_validation_ok() -> None:
    client = TestClient(app)
    payload = {
        "run_id": "run-123",
        "replay_timestamp": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
        "fixtures_processed": 1,
        "audit_schema_version": "v1",
        "integrity_hash": "abc",
    }
    resp = client.post("/api/v1/manifests/validate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["errors"] == []


def test_manifest_validation_malformed_request() -> None:
    client = TestClient(app)
    resp = client.post("/api/v1/manifests/validate", json={"run_id": "x"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["request_id"]


def test_diff_json_equal() -> None:
    client = TestClient(app)
    payload = {"left": [{"a": 1, "b": "x"}], "right": [{"a": 1, "b": "x"}]}
    resp = client.post("/api/v1/diff/json", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["result"]["status"] == "PASS"
    assert body["result"]["artifacts_equal"] is True


def test_diff_json_bad_payload() -> None:
    client = TestClient(app)
    payload = {"left": "not-a-row", "right": []}
    resp = client.post("/api/v1/diff/json", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["request_id"]


def test_diff_csv_equal() -> None:
    client = TestClient(app)
    payload = {"left_csv": "a,b\n1,x\n", "right_csv": "a,b\n1,x\n"}
    resp = client.post("/api/v1/diff/csv", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["status"] == "PASS"


def test_diff_csv_missing_header() -> None:
    client = TestClient(app)
    payload = {"left_csv": "", "right_csv": ""}
    resp = client.post("/api/v1/diff/csv", json=payload)
    assert resp.status_code == 400


def test_metrics_endpoint() -> None:
    client = TestClient(app)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "api_requests_total" in body
    assert "api_request_duration_seconds" in body
    assert "replay_validation_requests_total" in body
    assert "deterministic_diff_requests_total" in body


def test_metrics_can_be_disabled() -> None:
    app_disabled = create_app(AppSettings(enable_metrics=False))
    client = TestClient(app_disabled)
    resp = client.get("/metrics")
    assert resp.status_code == 404


def test_swagger_and_openapi_available() -> None:
    client = TestClient(app)
    docs = client.get("/docs")
    assert docs.status_code == 200
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    body = schema.json()
    assert body["info"]["title"]


def test_structured_logging_emits_request_id() -> None:
    formatter = JsonFormatter()
    try:
        set_request_id("req-logging-1")
        set_replay_run_id("run-123")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        record.event = "api.request"
        raw = formatter.format(record)
        obj = json.loads(raw)
        assert obj["event"] == "api.request"
        assert obj["request_id"] == "req-logging-1"
        assert obj["replay_run_id"] == "run-123"
    finally:
        set_request_id(None)
        set_replay_run_id(None)


def test_replay_run_create_retrieve_and_lineage(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "api.sqlite"
    url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)

    engine = create_engine(url)
    Base.metadata.create_all(engine)

    client = TestClient(app)
    payload = {
        "replay_type": "public_demo",
        "manifest_hash": "manifest-hash-1",
        "artifacts": [
            {"artifact_type": "manifest", "artifact_hash": "abc"},
            {"artifact_type": "audit", "artifact_hash": "def"},
        ],
    }
    created = client.post("/api/v1/replay/run", json=payload)
    assert created.status_code == 200
    created_body = created.json()
    run_id = created_body["run_id"]
    assert created_body["status"] == "created"

    fetched = client.get(f"/api/v1/replay/run/{run_id}")
    assert fetched.status_code == 200
    fetched_body = fetched.json()
    assert fetched_body["run_id"] == run_id
    assert fetched_body["replay_type"] == "public_demo"
    assert fetched_body["manifest_hash"] == "manifest-hash-1"
    assert fetched_body["request_id"]
    assert fetched_body["status"] == "created"

    lineage = client.get(f"/api/v1/lineage/{run_id}")
    assert lineage.status_code == 200
    lineage_body = lineage.json()
    assert lineage_body["ok"] is True
    assert lineage_body["record"]["run_id"] == run_id
    assert lineage_body["record"]["manifest_hash"] == "manifest-hash-1"
    assert len(lineage_body["record"]["artifacts"]) == 2


def test_replay_run_transaction_rolls_back(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "api.sqlite"
    url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)

    engine = create_engine(url)
    Base.metadata.create_all(engine)

    client = TestClient(app)
    run_id = str(uuid.uuid4())
    payload = {
        "run_id": run_id,
        "replay_type": "public_demo",
        "manifest_hash": "manifest-hash-1",
        "artifacts": [
            {"artifact_type": "manifest", "artifact_hash": "dup"},
            {"artifact_type": "manifest", "artifact_hash": "dup"},
        ],
    }
    created = client.post("/api/v1/replay/run", json=payload)
    assert created.status_code == 409

    fetched = client.get(f"/api/v1/replay/run/{run_id}")
    assert fetched.status_code == 404

    lineage = client.get(f"/api/v1/lineage/{run_id}")
    assert lineage.status_code == 404
