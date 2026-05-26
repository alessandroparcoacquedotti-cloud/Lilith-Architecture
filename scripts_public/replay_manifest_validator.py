"""
Public-Safe Replay Manifest Validator

Purpose
Validate replay manifests for replayable “as-if-live” execution cycles.

This utility is intentionally public-safe:
- No prediction logic
- No odds / betting outputs
- No production secrets
- No private thresholds
- No private dataset references

Example usage
    python scripts_public/replay_manifest_validator.py path/to/replay_manifest.json

    # Read manifest from stdin
    cat path/to/replay_manifest.json | python scripts_public/replay_manifest_validator.py -

    # PowerShell equivalent
    Get-Content path/to/replay_manifest.json | python scripts_public/replay_manifest_validator.py -
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


class ManifestValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    code: str
    message: str


REQUIRED_FIELDS: tuple[str, ...] = (
    "run_id",
    "replay_timestamp",
    "fixtures_processed",
    "audit_schema_version",
    "integrity_hash",
)


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _mask_value(value: str, keep_prefix: int = 8, keep_suffix: int = 4) -> str:
    # Avoid printing full identifiers/hashes in public logs. Keep just enough to correlate
    # artifacts across runs without revealing internal details.
    s = _safe_str(value)
    if not s:
        return ""
    if len(s) <= (keep_prefix + keep_suffix + 3):
        return "[REDACTED]"
    return f"{s[:keep_prefix]}...[REDACTED]...{s[-keep_suffix:]}"


def _load_manifest(path: str) -> dict[str, Any]:
    if path == "-":
        # Public-safe: allow stdin so users can validate manifests without writing temp files.
        raw = sys.stdin.read()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ManifestValidationError(f"SCHEMA ERROR: invalid JSON on stdin ({e.msg})") from e
    else:
        p = Path(path)
        if not p.exists():
            raise ManifestValidationError(f"SCHEMA ERROR: manifest file not found: {p}")
        try:
            raw = p.read_text(encoding="utf-8")
        except Exception as e:
            raise ManifestValidationError(f"SCHEMA ERROR: cannot read manifest file: {p}") from e
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ManifestValidationError(f"SCHEMA ERROR: invalid JSON ({e.msg})") from e

    if not isinstance(obj, dict):
        raise ManifestValidationError("SCHEMA ERROR: manifest root must be a JSON object")
    return obj


def _parse_iso8601_timestamp(value: Any) -> datetime:
    # Require timezone to make replay runs unambiguous (e.g., "Z" or "+00:00").
    s = _safe_str(value)
    if not s:
        raise ValueError("timestamp is empty")

    ts = s
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError as e:
        raise ValueError("timestamp is not valid ISO-8601") from e

    if dt.tzinfo is None:
        raise ValueError("timestamp must include timezone offset (e.g. Z or +00:00)")
    return dt


def _validate_required_fields(manifest: dict[str, Any]) -> list[Check]:
    checks: list[Check] = []
    missing = [k for k in REQUIRED_FIELDS if k not in manifest]
    if missing:
        for k in missing:
            checks.append(
                Check(
                    name=f"required_field:{k}",
                    status="FAIL",
                    code="MISSING FIELD",
                    message=f"Missing required field: {k}",
                )
            )
        return checks

    checks.append(
        Check(
            name="required_fields",
            status="PASS",
            code="OK",
            message="All required fields present",
        )
    )
    return checks


def _validate_field_types(manifest: dict[str, Any]) -> list[Check]:
    checks: list[Check] = []

    run_id = _safe_str(manifest.get("run_id"))
    if not run_id:
        checks.append(Check("type:run_id", "FAIL", "SCHEMA ERROR", "run_id must be a non-empty string"))
    else:
        checks.append(Check("type:run_id", "PASS", "OK", "run_id is present"))

    audit_schema_version = _safe_str(manifest.get("audit_schema_version"))
    if not audit_schema_version:
        checks.append(
            Check("type:audit_schema_version", "FAIL", "SCHEMA ERROR", "audit_schema_version must be a non-empty string")
        )
    else:
        checks.append(Check("type:audit_schema_version", "PASS", "OK", "audit_schema_version is present"))

    integrity_hash = _safe_str(manifest.get("integrity_hash"))
    if not integrity_hash:
        checks.append(Check("type:integrity_hash", "FAIL", "SCHEMA ERROR", "integrity_hash must be a non-empty string"))
    else:
        checks.append(Check("type:integrity_hash", "PASS", "OK", f"integrity_hash={_mask_value(integrity_hash)}"))

    fp = manifest.get("fixtures_processed")
    if isinstance(fp, bool) or fp is None:
        checks.append(
            Check("type:fixtures_processed", "FAIL", "SCHEMA ERROR", "fixtures_processed must be an integer >= 0")
        )
    elif isinstance(fp, int) and fp >= 0:
        checks.append(Check("type:fixtures_processed", "PASS", "OK", f"fixtures_processed={fp}"))
    else:
        try:
            fp_int = int(fp)
            if fp_int < 0:
                raise ValueError("negative")
            checks.append(Check("type:fixtures_processed", "PASS", "OK", f"fixtures_processed={fp_int}"))
        except Exception:
            checks.append(
                Check("type:fixtures_processed", "FAIL", "SCHEMA ERROR", "fixtures_processed must be an integer >= 0")
            )

    return checks


def _validate_timestamp(manifest: dict[str, Any]) -> list[Check]:
    checks: list[Check] = []
    try:
        dt = _parse_iso8601_timestamp(manifest.get("replay_timestamp"))
        checks.append(Check("timestamp:replay_timestamp", "PASS", "OK", f"replay_timestamp={dt.isoformat()}"))
    except Exception as e:
        checks.append(Check("timestamp:replay_timestamp", "FAIL", "INVALID TIMESTAMP", _safe_str(e)))
    return checks


def validate_manifest(manifest: dict[str, Any]) -> list[Check]:
    checks: list[Check] = []
    checks.extend(_validate_required_fields(manifest))
    if any(c.status == "FAIL" and c.code == "MISSING FIELD" for c in checks):
        return checks
    checks.extend(_validate_field_types(manifest))
    checks.extend(_validate_timestamp(manifest))
    return checks


def _print_report(manifest_path: str, checks: Iterable[Check]) -> int:
    checks_list = list(checks)
    failed = [c for c in checks_list if c.status == "FAIL"]
    status = "VALIDATION PASSED" if not failed else "VALIDATION FAILED"

    print("REPLAY_MANIFEST_VALIDATION")
    print(f"- manifest_path: {manifest_path}")
    print(f"- status: {status}")
    print(f"- checks_total: {len(checks_list)}")
    print(f"- checks_failed: {len(failed)}")
    print("")
    print("CHECKS")
    for c in checks_list:
        line = f"- {c.name}: {c.status}"
        print(line)
        print(f"  - code: {c.code}")
        print(f"  - message: {c.message}")
    print("")

    if not failed:
        return 0
    return 2


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="replay_manifest_validator",
        description="Validate a replay manifest for replayable as-if-live execution cycles (public-safe).",
    )
    p.add_argument(
        "manifest",
        help="Path to JSON replay manifest, or '-' to read from stdin.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        manifest = _load_manifest(args.manifest)
    except ManifestValidationError as e:
        print("REPLAY_MANIFEST_VALIDATION")
        print(f"- manifest_path: {args.manifest}")
        print("- status: SCHEMA ERROR")
        print(f"- message: {_safe_str(e)}")
        return 2

    checks = validate_manifest(manifest)
    return _print_report(args.manifest, checks)


if __name__ == "__main__":
    raise SystemExit(main())
