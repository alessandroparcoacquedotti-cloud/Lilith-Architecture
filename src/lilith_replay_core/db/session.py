from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TypeAlias

from sqlalchemy import create_engine as _create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

SessionMaker: TypeAlias = sessionmaker[Session]


def normalize_database_url(database_url: str) -> str:
    url = database_url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def create_engine(database_url: str, *, pool_pre_ping: bool = True) -> Engine:
    return _create_engine(normalize_database_url(database_url), pool_pre_ping=pool_pre_ping)


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it explicitly (for local dev: export it / set it in your shell, or provide it via Docker Compose)."
        )
    return value


def build_postgres_url_from_env() -> str:
    user = os.environ.get("POSTGRES_USER", "lilith")
    password = _get_required_env("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "lilith_replay")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


def create_engine_from_env(*, pool_pre_ping: bool = True) -> Engine:
    return create_engine(build_postgres_url_from_env(), pool_pre_ping=pool_pre_ping)


def create_sessionmaker(engine: Engine) -> SessionMaker:
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


@contextmanager
def session_scope(sessionmaker_: SessionMaker) -> Iterator[Session]:
    session = sessionmaker_()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
