from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from lilith_replay_core.diffing import DiffResult, compare_rows_csv_text, compare_rows_json
from lilith_replay_core.logging import get_logger
from lilith_replay_core.observability import (
    DETERMINISTIC_DIFF_REQUESTS_TOTAL,
    SCHEMA_DRIFT_DETECTED_TOTAL,
    counter_inc,
)

router = APIRouter(prefix="/diff", tags=["diffing"])
logger = get_logger(__name__)


class DiffOptions(BaseModel):
    collapse_whitespace: bool = True
    normalize_timestamps: bool = True
    primary_key: str | None = None
    max_items: int = Field(default=25, ge=1, le=500)


class JsonDiffRequest(BaseModel):
    left: Any
    right: Any
    options: DiffOptions = Field(default_factory=DiffOptions)


class CsvDiffRequest(BaseModel):
    left_csv: str
    right_csv: str
    options: DiffOptions = Field(default_factory=DiffOptions)


class ApiDiffResponse(BaseModel):
    ok: bool
    result: DiffResult


def _sanitize_result(result: DiffResult) -> DiffResult:
    details = dict(result.details)
    metadata = details.get("metadata")
    if isinstance(metadata, dict):
        details["metadata"] = {"tool": metadata.get("tool")}
    return DiffResult(
        artifacts_equal=result.artifacts_equal,
        schema_drift_detected=result.schema_drift_detected,
        normalized_hash_a=result.normalized_hash_a,
        normalized_hash_b=result.normalized_hash_b,
        diff_summary=result.diff_summary,
        status=result.status,
        details=details,
    )


@router.post("/json", response_model=ApiDiffResponse)
def diff_json(req: JsonDiffRequest) -> ApiDiffResponse:
    start = time.perf_counter()
    logger.info("diff request", extra={"event": "diff.request", "data": {"format": "json"}})
    try:
        result = compare_rows_json(
            left=req.left,
            right=req.right,
            primary_key=req.options.primary_key,
            collapse_whitespace=req.options.collapse_whitespace,
            normalize_timestamps=req.options.normalize_timestamps,
            max_items=req.options.max_items,
        )
    except ValueError as exc:
        counter_inc(DETERMINISTIC_DIFF_REQUESTS_TOTAL, format="json", status="bad_request")
        logger.warning("diff bad request", extra={"event": "diff.error", "data": {"format": "json"}})
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    status = result.status.lower().replace(" ", "_")
    counter_inc(DETERMINISTIC_DIFF_REQUESTS_TOTAL, format="json", status=status)
    if result.schema_drift_detected:
        counter_inc(SCHEMA_DRIFT_DETECTED_TOTAL, format="json")
    duration_ms = (time.perf_counter() - start) * 1000.0
    logger.info(
        "diff complete",
        extra={
            "event": "diff.result",
            "data": {
                "format": "json",
                "status": result.status,
                "schema_drift_detected": result.schema_drift_detected,
                "duration_ms": round(duration_ms, 3),
            },
        },
    )
    return ApiDiffResponse(ok=True, result=_sanitize_result(result))


@router.post("/csv", response_model=ApiDiffResponse)
def diff_csv(req: CsvDiffRequest) -> ApiDiffResponse:
    start = time.perf_counter()
    logger.info("diff request", extra={"event": "diff.request", "data": {"format": "csv"}})
    try:
        result = compare_rows_csv_text(
            left_csv=req.left_csv,
            right_csv=req.right_csv,
            primary_key=req.options.primary_key,
            collapse_whitespace=req.options.collapse_whitespace,
            normalize_timestamps=req.options.normalize_timestamps,
            max_items=req.options.max_items,
        )
    except ValueError as exc:
        counter_inc(DETERMINISTIC_DIFF_REQUESTS_TOTAL, format="csv", status="bad_request")
        logger.warning("diff bad request", extra={"event": "diff.error", "data": {"format": "csv"}})
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    status = result.status.lower().replace(" ", "_")
    counter_inc(DETERMINISTIC_DIFF_REQUESTS_TOTAL, format="csv", status=status)
    if result.schema_drift_detected:
        counter_inc(SCHEMA_DRIFT_DETECTED_TOTAL, format="csv")
    duration_ms = (time.perf_counter() - start) * 1000.0
    logger.info(
        "diff complete",
        extra={
            "event": "diff.result",
            "data": {
                "format": "csv",
                "status": result.status,
                "schema_drift_detected": result.schema_drift_detected,
                "duration_ms": round(duration_ms, 3),
            },
        },
    )
    return ApiDiffResponse(ok=True, result=_sanitize_result(result))
