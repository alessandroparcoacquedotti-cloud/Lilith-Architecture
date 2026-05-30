from __future__ import annotations

import argparse
import os
import time


def import_check() -> None:
    import lilith_replay_core
    import lilith_replay_core.diffing
    import lilith_replay_core.manifests
    import lilith_replay_core.validation

    _ = (
        lilith_replay_core,
        lilith_replay_core.diffing,
        lilith_replay_core.manifests,
        lilith_replay_core.validation,
    )


def db_check(database_url: str) -> None:
    try:
        from sqlalchemy import text
    except ModuleNotFoundError as exc:
        raise RuntimeError('DB extras not installed. Install with ".[db]".') from exc

    from lilith_replay_core.db.session import create_engine

    engine = create_engine(database_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lilith-replay-health")
    parser.add_argument("--db", action="store_true")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--stay-alive", action="store_true")
    parser.add_argument("--interval-seconds", type=float, default=10.0)
    args = parser.parse_args(argv)

    import_check()

    if args.db:
        database_url = args.database_url
        if not database_url:
            from lilith_replay_core.db.session import build_postgres_url_from_env

            database_url = build_postgres_url_from_env()
        db_check(database_url)

    if not args.stay_alive:
        return 0

    while True:
        time.sleep(max(args.interval_seconds, 0.5))


if __name__ == "__main__":
    raise SystemExit(main())
