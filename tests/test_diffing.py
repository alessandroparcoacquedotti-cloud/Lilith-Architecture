from __future__ import annotations

from pathlib import Path

from lilith_replay_core.diffing import compare_artifacts


def test_deterministic_hash_equality_json_examples() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    left = repo_root / "examples" / "artifacts" / "example_a.json"
    right = repo_root / "examples" / "artifacts" / "example_b.json"
    result = compare_artifacts(left_path=str(left), right_path=str(right))
    assert result.artifacts_equal
    assert result.normalized_hash_a == result.normalized_hash_b


def test_ordering_independent_comparison_csv_examples() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    left = repo_root / "examples" / "artifacts" / "example_a.csv"
    right = repo_root / "examples" / "artifacts" / "example_b.csv"
    result = compare_artifacts(left_path=str(left), right_path=str(right))
    assert result.artifacts_equal
    assert result.normalized_hash_a == result.normalized_hash_b


def test_schema_drift_detection(tmp_path: Path) -> None:
    left = tmp_path / "left.csv"
    right = tmp_path / "right.csv"
    left.write_text("id,name\n1,Alice\n2,Bob\n", encoding="utf-8")
    right.write_text("id,name,extra\n1,Alice,x\n2,Bob,y\n", encoding="utf-8")
    result = compare_artifacts(left_path=str(left), right_path=str(right))
    assert result.schema_drift_detected
    assert result.status == "SCHEMA DRIFT"
