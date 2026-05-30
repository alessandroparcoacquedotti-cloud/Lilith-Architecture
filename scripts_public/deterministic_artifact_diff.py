from __future__ import annotations

import argparse

from lilith_replay_core.diffing import compare_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="deterministic-artifact-diff")
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    args = parser.parse_args(argv)

    result = compare_artifacts(left_path=args.left, right_path=args.right)
    print(result.model_dump_json(indent=2))
    return 0 if result.artifacts_equal else 2


if __name__ == "__main__":
    raise SystemExit(main())
