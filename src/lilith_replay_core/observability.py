from __future__ import annotations

from types import ModuleType
from typing import Protocol, Self

_prom_module: ModuleType | None
try:
    import prometheus_client as _prom_module
except Exception:  # pragma: no cover
    _prom_module = None

_prom: ModuleType | None = _prom_module


class CounterLike(Protocol):
    def labels(self, **labels: str) -> Self: ...
    def inc(self, amount: float = 1.0) -> None: ...


class HistogramLike(Protocol):
    def labels(self, **labels: str) -> Self: ...
    def observe(self, amount: float) -> None: ...


def counter_inc(counter: CounterLike | None, **labels: str) -> None:
    if counter is None:
        return
    counter.labels(**labels).inc()


def counter_inc_unlabeled(counter: CounterLike | None) -> None:
    if counter is None:
        return
    counter.inc()


def hist_observe(hist: HistogramLike | None, value: float, **labels: str) -> None:
    if hist is None:
        return
    hist.labels(**labels).observe(value)


API_REQUESTS_TOTAL = (
    _prom.Counter(
        "api_requests_total",
        "Total API requests observed by the service.",
        labelnames=("method", "path", "status"),
    )
    if _prom is not None
    else None
)

API_REQUEST_DURATION_SECONDS = (
    _prom.Histogram(
        "api_request_duration_seconds",
        "API request latency in seconds.",
        labelnames=("method", "path", "status"),
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    )
    if _prom is not None
    else None
)

REPLAY_VALIDATION_REQUESTS_TOTAL = (
    _prom.Counter(
        "replay_validation_requests_total",
        "Total replay validation requests.",
        labelnames=("status",),
    )
    if _prom is not None
    else None
)

DETERMINISTIC_DIFF_REQUESTS_TOTAL = (
    _prom.Counter(
        "deterministic_diff_requests_total",
        "Total deterministic diff requests.",
        labelnames=("format", "status"),
    )
    if _prom is not None
    else None
)

VALIDATION_FAILURES_TOTAL = (
    _prom.Counter(
        "validation_failures_total",
        "Total validation failures.",
    )
    if _prom is not None
    else None
)

SCHEMA_DRIFT_DETECTED_TOTAL = (
    _prom.Counter(
        "schema_drift_detected_total",
        "Total schema drift detections in diff results.",
        labelnames=("format",),
    )
    if _prom is not None
    else None
)

API_STARTUPS_TOTAL = (
    _prom.Counter(
        "api_startups_total",
        "Total API startup events.",
    )
    if _prom is not None
    else None
)

DB_CONNECTIVITY_CHECKS_TOTAL = (
    _prom.Counter(
        "db_connectivity_checks_total",
        "Total database connectivity checks.",
        labelnames=("result",),
    )
    if _prom is not None
    else None
)

REPLAY_RUNS_CREATED_TOTAL = (
    _prom.Counter(
        "replay_runs_created_total",
        "Total replay runs created (committed).",
        labelnames=("replay_type", "status"),
    )
    if _prom is not None
    else None
)

ARTIFACT_RECORDS_CREATED_TOTAL = (
    _prom.Counter(
        "artifact_records_created_total",
        "Total artifact records persisted (committed).",
        labelnames=("artifact_type",),
    )
    if _prom is not None
    else None
)

LINEAGE_REQUESTS_TOTAL = (
    _prom.Counter(
        "lineage_requests_total",
        "Total lineage requests.",
        labelnames=("status",),
    )
    if _prom is not None
    else None
)

DB_TRANSACTIONS_TOTAL = (
    _prom.Counter(
        "db_transactions_total",
        "Total database operations executed by the service.",
        labelnames=("operation", "result"),
    )
    if _prom is not None
    else None
)

DB_OPERATION_DURATION_SECONDS = (
    _prom.Histogram(
        "db_operation_duration_seconds",
        "Database operation latency in seconds.",
        labelnames=("operation",),
        buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
    )
    if _prom is not None
    else None
)
