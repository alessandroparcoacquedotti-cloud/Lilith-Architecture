from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lilith_replay_core.validation import (
    load_manifest_from_json,
    validate_replay_manifest,
    validation_summary,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="replay-manifest-validator")
    parser.add_argument("manifest", help="Path to manifest JSON file, or '-' for stdin.")
    args = parser.parse_args(argv)

    if args.manifest == "-":
        raw = sys.stdin.read()
        manifest_source = "stdin"
    else:
        p = Path(args.manifest)
        raw = p.read_text(encoding="utf-8")
        manifest_source = str(p)

    manifest = load_manifest_from_json(raw)
    result = validate_replay_manifest(manifest)
    print(validation_summary(manifest_source, result))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
