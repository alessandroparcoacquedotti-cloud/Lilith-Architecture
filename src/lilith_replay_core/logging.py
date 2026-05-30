from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

_request_id_var: ContextVar[str | None] = ContextVar("lilith_request_id", default=None)
_replay_run_id_var: ContextVar[str | None] = ContextVar("lilith_replay_run_id", default=None)

_CONFIGURED = False


def get_request_id() -> str | None:
    return _request_id_var.get()


def set_request_id(request_id: str | None) -> None:
    _request_id_var.set(request_id)


def get_replay_run_id() -> str | None:
    return _replay_run_id_var.get()


def set_replay_run_id(replay_run_id: str | None) -> None:
    _replay_run_id_var.set(replay_run_id)


def _format_timestamp(created: float) -> str:
    ts = datetime.fromtimestamp(created, tz=UTC).isoformat(timespec="milliseconds")
    if ts.endswith("+00:00"):
        ts = f"{ts[:-6]}Z"
    return ts


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": _format_timestamp(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "replay_run_id": get_replay_run_id(),
        }

        event = getattr(record, "event", None)
        if isinstance(event, str) and event:
            payload["event"] = event

        http = getattr(record, "http", None)
        if isinstance(http, dict):
            payload["http"] = _json_safe(http)

        error = getattr(record, "error", None)
        if isinstance(error, dict):
            payload["error"] = _json_safe(error)

        data = getattr(record, "data", None)
        if isinstance(data, dict):
            payload["data"] = _json_safe(data)

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(level: int | str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter())

    for existing in list(root.handlers):
        root.removeHandler(existing)

    root.addHandler(handler)
    root.propagate = False

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True
        logger.setLevel(level)

    _CONFIGURED = True


def get_logger(name: str | None = None) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name if name else "lilith")

