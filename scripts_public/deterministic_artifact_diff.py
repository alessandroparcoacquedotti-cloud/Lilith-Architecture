"""
Public-Safe Deterministic Artifact Diff Utility

Purpose
Compare two replay/audit artifacts deterministically, producing stable ordering and reproducible diffs.

This utility is intentionally public-safe:
- No prediction logic
- No odds / betting logic
- No tuned thresholds
- No operational endpoints
- No private dataset references
- No raw value printing by default (diffs are hash-based)

Example usage
    python scripts_public/deterministic_artifact_diff.py --left artifact_a.csv --right artifact_b.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence


TOOL_NAME = "deterministic_artifact_diff"
TOOL_VERSION = "1.0.0"

JsonValue = Any
Status = Literal["PASS", "FAIL", "DIFF DETECTED", "SCHEMA DRIFT"]


class ArtifactDiffError(RuntimeError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _normalize_whitespace(s: str, *, collapse_internal: bool) -> str:
    s2 = s.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not collapse_internal:
        return s2
    return re.sub(r"\s+", " ", s2)


_ISO_LIKE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}([Tt ]\d{2}:\d{2}:\d{2}(\.\d{1,9})?([Zz]|[+-]\d{2}:\d{2})?)?$"
)
_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _looks_like_timestamp(value: str) -> bool:
    return bool(_ISO_LIKE_RE.match(value))


def _normalize_timestamp_string(value: str) -> str | None:
    s = value.strip()
    if not s:
        return None

    if _DATE_ONLY_RE.match(s):
        return s

    ts = s.replace(" ", "T")
    if ts.endswith("Z") or ts.endswith("z"):
        ts = ts[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None

    if dt.tzinfo is not None:
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.replace(tzinfo=None).isoformat(timespec="microseconds") + "Z"
    return dt.isoformat(timespec="microseconds")


def _normalize_decimal_str(d: Decimal) -> str:
    if d.is_zero():
        return "0"
    normalized = d.normalize()
    s = format(normalized, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s == "-0":
        return "0"
    return s


def _value_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, Decimal):
        return "decimal"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def _value_fingerprint(value: Any) -> dict[str, Any]:
    t = _value_type_name(value)
    if value is None:
        return {"type": t}
    if isinstance(value, bool):
        return {"type": t, "value": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"type": t, "value": value}
    if isinstance(value, Decimal):
        s = _normalize_decimal_str(value)
        return {"type": "decimal", "sha256": _sha256_text(s), "len": len(s)}
    if isinstance(value, float):
        s = repr(value)
        return {"type": "float", "sha256": _sha256_text(s), "len": len(s)}
    if isinstance(value, str):
        return {"type": "string", "sha256": _sha256_text(value), "len": len(value)}
    canonical = _stable_json_dumps(_jsonify(value))
    return {"type": t, "sha256": _sha256_text(canonical), "len": len(canonical)}


def _jsonify(value: Any) -> JsonValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, Decimal):
        return _normalize_decimal_str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    return _safe_str(value)


def _normalize_cell(
    value: Any,
    *,
    column_name: str,
    collapse_whitespace: bool,
    normalize_timestamps: bool,
) -> Any:
    if value is None:
        return None

    if isinstance(value, (bool, int, Decimal)):
        return value

    if isinstance(value, float):
        return Decimal(str(value))

    if isinstance(value, str):
        s0 = _normalize_whitespace(value, collapse_internal=collapse_whitespace)
        if s0 == "":
            return ""
        s_lower = s0.lower()
        if s_lower in {"null", "none", "nan"}:
            return None
        if normalize_timestamps and (_looks_like_timestamp(s0) or re.search(r"(time|timestamp|date|dt)$", column_name, re.I)):
            ts = _normalize_timestamp_string(s0)
            if ts is not None:
                return ts
        try:
            if re.fullmatch(r"[+-]?\d+", s0):
                return int(s0)
            if re.fullmatch(r"[+-]?(\d+\.\d*|\d*\.\d+)", s0):
                return Decimal(s0)
        except (InvalidOperation, ValueError):
            pass
        return s0

    if isinstance(value, dict):
        return {str(k): _normalize_cell(v, column_name=column_name, collapse_whitespace=collapse_whitespace, normalize_timestamps=normalize_timestamps) for k, v in value.items()}

    if isinstance(value, list):
        return [_normalize_cell(v, column_name=column_name, collapse_whitespace=collapse_whitespace, normalize_timestamps=normalize_timestamps) for v in value]

    return _normalize_cell(_safe_str(value), column_name=column_name, collapse_whitespace=collapse_whitespace, normalize_timestamps=normalize_timestamps)


def _canonical_row_bytes(row: Mapping[str, Any], columns: Sequence[str]) -> bytes:
    obj = {c: _jsonify(row.get(c)) for c in columns}
    return _stable_json_dumps(obj).encode("utf-8")


def _row_hash(row: Mapping[str, Any], columns: Sequence[str]) -> str:
    return _sha256_bytes(_canonical_row_bytes(row, columns))


def _schema_hash(columns: Sequence[str]) -> str:
    return _sha256_text(_stable_json_dumps({"columns": list(columns)}))


def _stable_path_label(path: str) -> dict[str, str]:
    p = Path(path)
    return {"name": p.name, "path_sha256": _sha256_text(str(p.resolve()))}


def _read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except Exception as e:
        raise ArtifactDiffError(f"cannot read file: {path} ({_safe_str(e)})") from e


def _detect_format(path: str, raw_text: str) -> Literal["csv", "json"]:
    ext = Path(path).suffix.lower()
    if ext == ".csv":
        return "csv"
    if ext == ".json":
        return "json"
    s = raw_text.lstrip()
    if s.startswith("{") or s.startswith("["):
        return "json"
    return "csv"


def _load_csv(path: str) -> list[dict[str, Any]]:
    raw = _read_text(path)
    rows: list[dict[str, Any]] = []
    try:
        reader = csv.DictReader(raw.splitlines())
    except Exception as e:
        raise ArtifactDiffError(f"invalid CSV: {path} ({_safe_str(e)})") from e
    if reader.fieldnames is None:
        return []
    for r in reader:
        row: dict[str, Any] = {}
        for k, v in r.items():
            if k is None:
                continue
            row[str(k)] = v
        rows.append(row)
    return rows


def _load_json(path: str) -> list[dict[str, Any]]:
    raw = _read_text(path)
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ArtifactDiffError(f"invalid JSON: {path} ({e.msg})") from e

    if isinstance(obj, list):
        items = obj
    elif isinstance(obj, dict):
        for k in ("rows", "records", "data", "items"):
            if isinstance(obj.get(k), list):
                items = obj[k]
                break
        else:
            items = [obj]
    else:
        raise ArtifactDiffError("JSON root must be an object or array")

    rows: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            rows.append({str(k): v for k, v in item.items()})
        else:
            rows.append({"_value": item, "_index": i})
    return rows


def _load_artifact_rows(path: str) -> tuple[Literal["csv", "json"], list[dict[str, Any]]]:
    raw = _read_text(path)
    fmt = _detect_format(path, raw)
    if fmt == "csv":
        return fmt, _load_csv(path)
    return fmt, _load_json(path)


def _collect_columns(rows: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    cols: set[str] = set()
    for r in rows:
        cols.update(str(k) for k in r.keys())
    return tuple(sorted(cols))


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    types: tuple[str, ...]
    non_null: int


@dataclass(frozen=True)
class ArtifactNormalized:
    label: dict[str, str]
    format: Literal["csv", "json"]
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    schema_hash: str
    content_hash: str
    column_profiles: tuple[ColumnProfile, ...]


def _infer_column_profiles(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> tuple[ColumnProfile, ...]:
    profiles: list[ColumnProfile] = []
    for c in columns:
        types: set[str] = set()
        non_null = 0
        for r in rows:
            v = r.get(c)
            if v is None:
                types.add("null")
                continue
            non_null += 1
            types.add(_value_type_name(v))
        profiles.append(ColumnProfile(name=c, types=tuple(sorted(types)), non_null=non_null))
    return tuple(profiles)


def normalize_artifact(
    path: str,
    *,
    collapse_whitespace: bool,
    normalize_timestamps: bool,
    force_columns: Sequence[str] | None,
) -> ArtifactNormalized:
    fmt, raw_rows = _load_artifact_rows(path)

    columns = tuple(force_columns) if force_columns is not None else _collect_columns(raw_rows)
    norm_rows: list[dict[str, Any]] = []
    for r in raw_rows:
        nr: dict[str, Any] = {}
        for c in columns:
            nr[c] = _normalize_cell(
                r.get(c),
                column_name=c,
                collapse_whitespace=collapse_whitespace,
                normalize_timestamps=normalize_timestamps,
            )
        norm_rows.append(nr)

    row_hashes = [_row_hash(r, columns) for r in norm_rows]
    content_hasher = hashlib.sha256()
    for h in sorted(row_hashes):
        content_hasher.update(h.encode("ascii"))
        content_hasher.update(b"\n")

    profiles = _infer_column_profiles(norm_rows, columns)
    return ArtifactNormalized(
        label=_stable_path_label(path),
        format=fmt,
        columns=columns,
        rows=tuple(norm_rows),
        schema_hash=_schema_hash(columns),
        content_hash=content_hasher.hexdigest(),
        column_profiles=profiles,
    )


def _parse_primary_key(spec: str | None) -> tuple[str, ...]:
    if spec is None:
        return ()
    parts = [p.strip() for p in spec.split(",")]
    return tuple(p for p in parts if p)


def _infer_primary_key(common_columns: Sequence[str], left_rows: Sequence[Mapping[str, Any]], right_rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    candidates: list[str] = []
    for c in common_columns:
        cl = c.lower()
        if cl in {"id", "uuid", "key", "pk", "record_id"} or cl.endswith("_id"):
            candidates.append(c)
    candidates = sorted(set(candidates))

    def is_unique_within(rows: Sequence[Mapping[str, Any]], col: str) -> bool:
        seen: set[str] = set()
        for r in rows:
            v = r.get(col)
            if v is None:
                return False
            key = _stable_json_dumps(_jsonify(v))
            if key in seen:
                return False
            seen.add(key)
        return bool(seen)

    for c in candidates:
        if is_unique_within(left_rows, c) and is_unique_within(right_rows, c):
            return (c,)
    return ()


def _build_key_map(
    rows: Sequence[Mapping[str, Any]],
    *,
    key_columns: Sequence[str],
    columns: Sequence[str],
) -> tuple[dict[tuple[str, ...], Mapping[str, Any]], list[tuple[str, ...]]]:
    mp: dict[tuple[str, ...], Mapping[str, Any]] = {}
    dups: list[tuple[str, ...]] = []
    for r in rows:
        key = tuple(_stable_json_dumps(_jsonify(r.get(c))) for c in key_columns)
        if key in mp:
            dups.append(key)
            continue
        mp[key] = r
    return mp, dups


def _key_digest(key: tuple[str, ...]) -> str:
    return _sha256_text(_stable_json_dumps(list(key)))


@dataclass(frozen=True)
class DiffFindings:
    status: Status
    schema: dict[str, Any]
    row_diff: dict[str, Any]
    hashes: dict[str, Any]
    metadata: dict[str, Any]


def diff_artifacts(
    left: ArtifactNormalized,
    right: ArtifactNormalized,
    *,
    primary_key: tuple[str, ...],
    max_items: int,
) -> DiffFindings:
    left_cols = set(left.columns)
    right_cols = set(right.columns)
    common_cols = tuple(sorted(left_cols & right_cols))
    only_left = tuple(sorted(left_cols - right_cols))
    only_right = tuple(sorted(right_cols - left_cols))

    left_profiles = {p.name: p for p in left.column_profiles}
    right_profiles = {p.name: p for p in right.column_profiles}
    type_mismatches: list[dict[str, Any]] = []
    for c in common_cols:
        lt = left_profiles[c].types
        rt = right_profiles[c].types
        lt_non_null = tuple(t for t in lt if t != "null")
        rt_non_null = tuple(t for t in rt if t != "null")
        if lt_non_null != rt_non_null:
            type_mismatches.append(
                {
                    "column": c,
                    "left_types": lt,
                    "right_types": rt,
                    "left_non_null_types": lt_non_null,
                    "right_non_null_types": rt_non_null,
                }
            )

    schema_drift = bool(only_left or only_right or type_mismatches)
    schema = {
        "left_columns": list(left.columns),
        "right_columns": list(right.columns),
        "only_left": list(only_left),
        "only_right": list(only_right),
        "type_mismatches": type_mismatches,
    }

    pk = primary_key
    if not pk:
        pk = _infer_primary_key(common_cols, left.rows, right.rows)

    row_diff: dict[str, Any]
    if pk:
        lmap, ldups = _build_key_map(left.rows, key_columns=pk, columns=left.columns)
        rmap, rdups = _build_key_map(right.rows, key_columns=pk, columns=right.columns)
        key_duplicates = sorted({_key_digest(k) for k in (ldups + rdups)})
        if key_duplicates:
            pk = ()
            row_diff = {"mode": "multiset", "note": "primary key had duplicates; fell back to multiset diff", "primary_key": list(primary_key)}
        else:
            lkeys = set(lmap.keys())
            rkeys = set(rmap.keys())
            added_keys = sorted((_key_digest(k) for k in (rkeys - lkeys)))
            removed_keys = sorted((_key_digest(k) for k in (lkeys - rkeys)))
            shared_keys = sorted(lkeys & rkeys)

            changed: list[dict[str, Any]] = []
            for k in shared_keys:
                lr = lmap[k]
                rr = rmap[k]
                lh = _row_hash(lr, left.columns)
                rh = _row_hash(rr, right.columns)
                if lh == rh:
                    continue
                changed_columns: list[dict[str, Any]] = []
                for c in sorted(set(left.columns) | set(right.columns)):
                    lv = lr.get(c)
                    rv = rr.get(c)
                    if _stable_json_dumps(_jsonify(lv)) == _stable_json_dumps(_jsonify(rv)):
                        continue
                    changed_columns.append(
                        {
                            "column": c,
                            "left": _value_fingerprint(lv),
                            "right": _value_fingerprint(rv),
                        }
                    )
                changed.append(
                    {
                        "key_sha256": _key_digest(k),
                        "left_row_sha256": lh,
                        "right_row_sha256": rh,
                        "changed_columns": changed_columns[:max_items],
                        "changed_columns_total": len(changed_columns),
                    }
                )

            row_diff = {
                "mode": "primary_key",
                "primary_key": list(pk),
                "rows_left": len(left.rows),
                "rows_right": len(right.rows),
                "added_rows": len(added_keys),
                "removed_rows": len(removed_keys),
                "changed_rows": len(changed),
                "added_key_sha256_sample": added_keys[:max_items],
                "removed_key_sha256_sample": removed_keys[:max_items],
                "changed_rows_sample": changed[:max_items],
            }
    if not pk:
        left_hashes = [_row_hash(r, left.columns) for r in left.rows]
        right_hashes = [_row_hash(r, right.columns) for r in right.rows]
        lc = Counter(left_hashes)
        rc = Counter(right_hashes)
        added: list[str] = []
        removed: list[str] = []
        for h in sorted(set(lc) | set(rc)):
            dv = rc.get(h, 0) - lc.get(h, 0)
            if dv > 0:
                added.extend([h] * dv)
            elif dv < 0:
                removed.extend([h] * (-dv))

        row_diff = {
            "mode": "multiset",
            "primary_key": [],
            "rows_left": len(left.rows),
            "rows_right": len(right.rows),
            "added_rows": len(added),
            "removed_rows": len(removed),
            "changed_rows": 0,
            "added_row_sha256_sample": sorted(added)[:max_items],
            "removed_row_sha256_sample": sorted(removed)[:max_items],
        }

    diffs_exist = (
        schema_drift
        or row_diff.get("added_rows", 0) > 0
        or row_diff.get("removed_rows", 0) > 0
        or row_diff.get("changed_rows", 0) > 0
        or left.content_hash != right.content_hash
        or left.schema_hash != right.schema_hash
    )

    if schema_drift:
        status: Status = "SCHEMA DRIFT"
    elif diffs_exist:
        status = "DIFF DETECTED"
    else:
        status = "PASS"

    hashes = {
        "left": {"schema_sha256": left.schema_hash, "content_sha256": left.content_hash},
        "right": {"schema_sha256": right.schema_hash, "content_sha256": right.content_hash},
        "equal": {"schema": left.schema_hash == right.schema_hash, "content": left.content_hash == right.content_hash},
    }

    metadata = {
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "runtime": {"python": sys.version.split()[0], "platform": platform.platform()},
        "artifacts": {"left": left.label, "right": right.label},
        "diff_mode": row_diff.get("mode"),
        "primary_key_used": row_diff.get("primary_key", []),
        "max_items": max_items,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    return DiffFindings(status=status, schema=schema, row_diff=row_diff, hashes=hashes, metadata=metadata)


def _print_human_report(findings: DiffFindings) -> None:
    print("DETERMINISTIC_ARTIFACT_DIFF")
    print(f"- status: {findings.status}")
    print(f"- left: {findings.metadata['artifacts']['left']['name']}")
    print(f"- right: {findings.metadata['artifacts']['right']['name']}")
    print(f"- diff_mode: {findings.metadata['diff_mode']}")
    pk = findings.metadata.get("primary_key_used", [])
    print(f"- primary_key_used: {', '.join(pk) if pk else '(none)'}")
    print("")

    print("HASHES")
    for side in ("left", "right"):
        print(f"- {side}.schema_sha256: {findings.hashes[side]['schema_sha256']}")
        print(f"- {side}.content_sha256: {findings.hashes[side]['content_sha256']}")
    print(f"- equal.schema: {findings.hashes['equal']['schema']}")
    print(f"- equal.content: {findings.hashes['equal']['content']}")
    print("")

    if findings.schema["only_left"] or findings.schema["only_right"] or findings.schema["type_mismatches"]:
        print("SCHEMA")
        if findings.schema["only_left"]:
            print(f"- columns_only_in_left: {len(findings.schema['only_left'])}")
        if findings.schema["only_right"]:
            print(f"- columns_only_in_right: {len(findings.schema['only_right'])}")
        if findings.schema["type_mismatches"]:
            print(f"- type_mismatches: {len(findings.schema['type_mismatches'])}")
        print("")

    rd = findings.row_diff
    print("ROW_DIFF")
    print(f"- rows_left: {rd.get('rows_left')}")
    print(f"- rows_right: {rd.get('rows_right')}")
    print(f"- added_rows: {rd.get('added_rows')}")
    print(f"- removed_rows: {rd.get('removed_rows')}")
    print(f"- changed_rows: {rd.get('changed_rows')}")

    if rd.get("mode") == "primary_key":
        if rd.get("added_key_sha256_sample"):
            print(f"- added_key_sha256_sample: {', '.join(rd['added_key_sha256_sample'])}")
        if rd.get("removed_key_sha256_sample"):
            print(f"- removed_key_sha256_sample: {', '.join(rd['removed_key_sha256_sample'])}")
        if rd.get("changed_rows_sample"):
            print(f"- changed_rows_sample: {len(rd['changed_rows_sample'])} (see --json for details)")
    else:
        if rd.get("added_row_sha256_sample"):
            print(f"- added_row_sha256_sample: {', '.join(rd['added_row_sha256_sample'])}")
        if rd.get("removed_row_sha256_sample"):
            print(f"- removed_row_sha256_sample: {', '.join(rd['removed_row_sha256_sample'])}")
    print("")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Deterministically diff two replay/audit artifacts (CSV/JSON) with stable ordering and public-safe output.",
    )
    p.add_argument("--left", required=True, help="Path to left artifact (CSV or JSON).")
    p.add_argument("--right", required=True, help="Path to right artifact (CSV or JSON).")
    p.add_argument("--primary-key", default=None, help="Comma-separated column list to match rows (e.g. id,run_id).")
    p.add_argument("--no-collapse-whitespace", action="store_true", help="Do not collapse internal whitespace in strings.")
    p.add_argument("--no-normalize-timestamps", action="store_true", help="Do not normalize ISO-like timestamps.")
    p.add_argument("--max-items", type=int, default=25, help="Max number of sample items emitted in reports.")
    p.add_argument("--json", action="store_true", help="Print machine-readable JSON audit summary to stdout.")
    p.add_argument("--json-out", default=None, help="Write machine-readable JSON audit summary to a file.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.max_items <= 0:
        raise SystemExit("--max-items must be >= 1")

    collapse_whitespace = not bool(args.no_collapse_whitespace)
    normalize_timestamps = not bool(args.no_normalize_timestamps)
    primary_key = _parse_primary_key(args.primary_key)

    try:
        left_fmt, left_raw = _load_artifact_rows(args.left)
        right_fmt, right_raw = _load_artifact_rows(args.right)
        all_columns = tuple(sorted(set(_collect_columns(left_raw)) | set(_collect_columns(right_raw))))
        left_norm = normalize_artifact(
            args.left,
            collapse_whitespace=collapse_whitespace,
            normalize_timestamps=normalize_timestamps,
            force_columns=all_columns,
        )
        right_norm = normalize_artifact(
            args.right,
            collapse_whitespace=collapse_whitespace,
            normalize_timestamps=normalize_timestamps,
            force_columns=all_columns,
        )
        left_norm = ArtifactNormalized(
            label=left_norm.label,
            format=left_fmt,
            columns=left_norm.columns,
            rows=left_norm.rows,
            schema_hash=left_norm.schema_hash,
            content_hash=left_norm.content_hash,
            column_profiles=left_norm.column_profiles,
        )
        right_norm = ArtifactNormalized(
            label=right_norm.label,
            format=right_fmt,
            columns=right_norm.columns,
            rows=right_norm.rows,
            schema_hash=right_norm.schema_hash,
            content_hash=right_norm.content_hash,
            column_profiles=right_norm.column_profiles,
        )
    except ArtifactDiffError as e:
        print("DETERMINISTIC_ARTIFACT_DIFF")
        print("- status: FAIL")
        print(f"- message: {_safe_str(e)}")
        return 2

    findings = diff_artifacts(left_norm, right_norm, primary_key=primary_key, max_items=args.max_items)
    _print_human_report(findings)

    payload = {
        "status": findings.status,
        "schema": findings.schema,
        "row_diff": findings.row_diff,
        "hashes": findings.hashes,
        "metadata": findings.metadata,
    }
    if args.json:
        print(_stable_json_dumps(payload))
        print("")

    if args.json_out:
        try:
            Path(args.json_out).write_text(_stable_json_dumps(payload) + "\n", encoding="utf-8")
        except Exception as e:
            print("DETERMINISTIC_ARTIFACT_DIFF")
            print("- status: FAIL")
            print(f"- message: cannot write --json-out ({_safe_str(e)})")
            return 2

    if findings.status == "PASS":
        return 0
    if findings.status == "DIFF DETECTED":
        return 1
    if findings.status == "SCHEMA DRIFT":
        return 3
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
