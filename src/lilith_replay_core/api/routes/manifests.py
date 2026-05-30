from __future__ import annotations

import time

from fastapi import APIRouter

from lilith_replay_core.logging import get_logger, set_replay_run_id
from lilith_replay_core.manifests import ReplayManifest
from lilith_replay_core.observability import (
    REPLAY_VALIDATION_REQUESTS_TOTAL,
    VALIDATION_FAILURES_TOTAL,
    counter_inc,
    counter_inc_unlabeled,
)
from lilith_replay_core.validation import ValidationResult, validate_replay_manifest

router = APIRouter(prefix="/manifests", tags=["manifests"])
logger = get_logger(__name__)


@router.post("/validate", response_model=ValidationResult)
def validate_manifest(manifest: ReplayManifest) -> ValidationResult:
    set_replay_run_id(manifest.run_id)
    start = time.perf_counter()
    logger.info("validation request", extra={"event": "validation.request", "data": {"replay_run_id": manifest.run_id}})
    result = validate_replay_manifest(manifest)
    duration_ms = (time.perf_counter() - start) * 1000.0

    status = "pass" if result.ok else "fail"
    counter_inc(REPLAY_VALIDATION_REQUESTS_TOTAL, status=status)
    if not result.ok:
        counter_inc_unlabeled(VALIDATION_FAILURES_TOTAL)

    logger.info(
        "validation complete",
        extra={
            "event": "validation.result",
            "data": {
                "replay_run_id": manifest.run_id,
                "ok": result.ok,
                "error_count": len(result.errors),
                "warning_count": len(result.warnings),
                "duration_ms": round(duration_ms, 3),
            },
        },
    )
    return ValidationResult(ok=result.ok, errors=sorted(result.errors), warnings=sorted(result.warnings))
