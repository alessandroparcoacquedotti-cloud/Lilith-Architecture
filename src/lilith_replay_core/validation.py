from __future__ import annotations

import json
from datetime import UTC
from pathlib import Path

from pydantic import BaseModel, Field

from .manifests import ReplayManifest


class ValidationResult(BaseModel):
    ok: bool = Field(..., description="Whether validation succeeded.")
    errors: list[str] = Field(default_factory=list, description="Validation errors.")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal validation warnings.")


def load_manifest_from_json(raw_json: str) -> ReplayManifest:
    obj = json.loads(raw_json)
    if not isinstance(obj, dict):
        raise ValueError("manifest root must be a JSON object")
    return ReplayManifest.model_validate(obj)


def load_manifest_from_file(path: str | Path) -> ReplayManifest:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    return load_manifest_from_json(raw)


def validation_summary(manifest_source: str, result: ValidationResult) -> str:
    lines: list[str] = []
    status = "VALIDATION PASSED" if result.ok else "VALIDATION FAILED"
    lines.append("REPLAY_MANIFEST_VALIDATION")
    lines.append(f"- manifest_source: {manifest_source}")
    lines.append(f"- status: {status}")
    lines.append(f"- errors: {len(result.errors)}")
    lines.append(f"- warnings: {len(result.warnings)}")
    if result.errors:
        lines.append("")
        lines.append("ERRORS")
        for msg in sorted(result.errors):
            lines.append(f"- {msg}")
    if result.warnings:
        lines.append("")
        lines.append("WARNINGS")
        for msg in sorted(result.warnings):
            lines.append(f"- {msg}")
    lines.append("")
    return "\n".join(lines)


def validate_replay_manifest(manifest: ReplayManifest) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not manifest.run_id.strip():
        errors.append("run_id must be non-empty.")

    if manifest.fixtures_processed < 0:
        errors.append("fixtures_processed must be >= 0.")

    if not manifest.audit_schema_version.strip():
        errors.append("audit_schema_version must be non-empty.")

    if not manifest.integrity_hash.strip():
        warnings.append("integrity_hash is empty.")

    if manifest.replay_timestamp.tzinfo is None:
        errors.append("replay_timestamp must include timezone offset (e.g. Z or +00:00).")
    else:
        if manifest.replay_timestamp.astimezone(UTC) != manifest.replay_timestamp:
            warnings.append("replay_timestamp is not UTC; ensure deterministic normalization to UTC.")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)
