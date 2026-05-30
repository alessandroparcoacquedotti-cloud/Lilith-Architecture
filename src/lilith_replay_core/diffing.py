from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class DiffResult(BaseModel):
    artifacts_equal: bool = Field(..., description="True when normalized artifacts are equal.")
    schema_drift_detected: bool = Field(..., description="True when schema drift was detected.")
    normalized_hash_a: str = Field(..., description="Deterministic content hash of normalized left artifact.")
    normalized_hash_b: str = Field(..., description="Deterministic content hash of normalized right artifact.")
    diff_summary: str = Field(..., description="Deterministic human-readable summary.")
    status: Literal["PASS", "DIFF DETECTED", "SCHEMA DRIFT", "FAIL"] = Field(...)
    details: dict[str, Any] = Field(default_factory=dict)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _normalize_json_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise ValueError("json diff requires left/right to be list[object]")
    normalized: list[dict[str, Any]] = []
    for r in rows:
        normalized.append({str(k): r[k] for k in sorted(r.keys(), key=str)})
    return normalized


def _hash_json_rows(rows: list[dict[str, Any]]) -> str:
    canon = [_stable_json_dumps(r) for r in rows]
    canon_sorted = sorted(canon)
    return _sha256_text(_stable_json_dumps(canon_sorted))


def compare_rows_json(
    *,
    left: Any,
    right: Any,
    primary_key: str | None = None,
    collapse_whitespace: bool = True,
    normalize_timestamps: bool = True,
    max_items: int = 25,
) -> DiffResult:
    _ = (primary_key, collapse_whitespace, normalize_timestamps, max_items)
    left_rows = _normalize_json_rows(left)
    right_rows = _normalize_json_rows(right)

    left_hash = _hash_json_rows(left_rows)
    right_hash = _hash_json_rows(right_rows)
    equal = left_hash == right_hash

    return DiffResult(
        artifacts_equal=equal,
        schema_drift_detected=False,
        normalized_hash_a=left_hash,
        normalized_hash_b=right_hash,
        diff_summary="PASS" if equal else "DIFF DETECTED",
        status="PASS" if equal else "DIFF DETECTED",
        details={"metadata": {"tool": {"name": "deterministic_artifact_diff", "version": "1.0.0"}}},
    )


def _parse_csv(text: str) -> tuple[list[str], list[dict[str, str]]]:
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.DictReader(io.StringIO(s))
    if reader.fieldnames is None or not any((n or "").strip() for n in reader.fieldnames):
        raise ValueError("csv diff requires a header row")
    columns = [str(c) for c in reader.fieldnames]
    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append({str(k): "" if row[k] is None else str(row[k]) for k in columns})
    return columns, rows


def _hash_csv(columns: list[str], rows: list[dict[str, str]]) -> str:
    canon_rows = [_stable_json_dumps({c: rows[i].get(c, "") for c in columns}) for i in range(len(rows))]
    canon_rows_sorted = sorted(canon_rows)
    obj = {"columns": columns, "rows": canon_rows_sorted}
    return _sha256_text(_stable_json_dumps(obj))


def compare_rows_csv_text(
    *,
    left_csv: str,
    right_csv: str,
    primary_key: str | None = None,
    collapse_whitespace: bool = True,
    normalize_timestamps: bool = True,
    max_items: int = 25,
) -> DiffResult:
    _ = (primary_key, collapse_whitespace, normalize_timestamps, max_items)
    left_cols, left_rows = _parse_csv(left_csv)
    right_cols, right_rows = _parse_csv(right_csv)

    schema_drift = left_cols != right_cols
    left_hash = _hash_csv(left_cols, left_rows)
    right_hash = _hash_csv(right_cols, right_rows)
    equal = (not schema_drift) and (left_hash == right_hash)

    if schema_drift:
        status: Literal["PASS", "DIFF DETECTED", "SCHEMA DRIFT", "FAIL"] = "SCHEMA DRIFT"
        summary = "SCHEMA DRIFT"
    elif equal:
        status = "PASS"
        summary = "PASS"
    else:
        status = "DIFF DETECTED"
        summary = "DIFF DETECTED"

    return DiffResult(
        artifacts_equal=equal,
        schema_drift_detected=schema_drift,
        normalized_hash_a=left_hash,
        normalized_hash_b=right_hash,
        diff_summary=summary,
        status=status,
        details={"metadata": {"tool": {"name": "deterministic_artifact_diff", "version": "1.0.0"}}},
    )


def compare_artifacts(*, left_path: str, right_path: str) -> DiffResult:
    left_p = Path(left_path)
    right_p = Path(right_path)
    left_text = left_p.read_text(encoding="utf-8-sig")
    right_text = right_p.read_text(encoding="utf-8-sig")

    if left_p.suffix.lower() == ".csv" and right_p.suffix.lower() == ".csv":
        return compare_rows_csv_text(left_csv=left_text, right_csv=right_text)
    if left_p.suffix.lower() == ".json" and right_p.suffix.lower() == ".json":
        left_obj = json.loads(left_text)
        right_obj = json.loads(right_text)
        return compare_rows_json(left=left_obj, right=right_obj)

    raise ValueError("artifacts must be both .csv or both .json")

