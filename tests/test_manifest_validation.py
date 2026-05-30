from __future__ import annotations

import json
from pathlib import Path

import pytest

from lilith_replay_core.validation import load_manifest_from_file, load_manifest_from_json, validate_replay_manifest


def test_manifest_validation_success() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest = load_manifest_from_file(repo_root / "examples" / "replay_manifest_valid.json")
    result = validate_replay_manifest(manifest)
    assert result.ok
    assert result.errors == []


def test_malformed_json_handling() -> None:
    with pytest.raises(json.JSONDecodeError):
        load_manifest_from_json("{")
