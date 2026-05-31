from __future__ import annotations

import os
from functools import lru_cache

from lilith_replay_core.db.session import (
    SessionMaker,
    build_postgres_url_from_env,
    create_engine,
    create_sessionmaker,
)


def resolve_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if isinstance(database_url, str) and database_url.strip():
        return database_url.strip()
    if os.environ.get("POSTGRES_HOST"):
        return build_postgres_url_from_env()
    raise RuntimeError("Database not configured (set DATABASE_URL or POSTGRES_* environment variables).")


@lru_cache(maxsize=8)
def get_sessionmaker(database_url: str) -> SessionMaker:
    engine = create_engine(database_url)
    return create_sessionmaker(engine)
