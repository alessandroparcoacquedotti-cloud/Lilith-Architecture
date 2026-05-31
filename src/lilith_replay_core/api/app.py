from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

from lilith_replay_core import __version__
from lilith_replay_core.api.routes import diffing, health, lineage, manifests, replay
from lilith_replay_core.config import AppSettings, load_settings
from lilith_replay_core.logging import (
    configure_logging,
    get_logger,
    get_replay_run_id,
    get_request_id,
    set_replay_run_id,
    set_request_id,
)
from lilith_replay_core.observability import (
    API_REQUEST_DURATION_SECONDS,
    API_REQUESTS_TOTAL,
    API_STARTUPS_TOTAL,
    counter_inc,
    counter_inc_unlabeled,
    hist_observe,
)

try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    generate_latest = None  # type: ignore[assignment]


def create_app(settings: AppSettings | None = None) -> FastAPI:
    resolved = load_settings() if settings is None else settings
    configure_logging(resolved.log_level)
    logger = get_logger(__name__)

    app = FastAPI(
        title="Lilith Replay Platform (Public)",
        description=(
            "Public-safe deterministic replay infrastructure for validation engineering and governance. "
            "This service exposes reproducible validation and deterministic diffing primitives for replay artifacts. "
            "No prediction logic, betting logic, private datasets, secrets, or operational thresholds are exposed."
        ),
        version=__version__,
        contact={"name": "Lilith Maintainers", "email": "maintainers@example.invalid", "url": "https://example.invalid"},
        license_info={"name": "TBD", "url": "https://example.invalid"},
    )

    @app.on_event("startup")
    def _on_startup() -> None:
        counter_inc_unlabeled(API_STARTUPS_TOTAL)
        logger.info(
            "boot",
            extra={
                "event": "api.boot",
                "data": {"app_env": resolved.app_env, "version": __version__, "enable_metrics": resolved.enable_metrics},
            },
        )
        logger.info("startup", extra={"event": "api.startup"})

    @app.on_event("shutdown")
    def _on_shutdown() -> None:
        logger.info("shutdown", extra={"event": "api.shutdown"})

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        request_id = get_request_id()
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "request_id": request_id},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = get_request_id()
        return JSONResponse(
            status_code=422,
            content={"detail": "validation_error", "request_id": request_id, "errors": exc.errors()},
        )

    @app.middleware("http")
    async def _request_context_middleware(
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        inbound = request.headers.get("X-Request-ID")
        request_id = inbound.strip() if isinstance(inbound, str) and inbound.strip() else uuid.uuid4().hex

        prev_request_id = get_request_id()
        prev_replay_run_id = get_replay_run_id()
        set_request_id(request_id)
        set_replay_run_id(None)

        start = time.perf_counter()
        response: Response | None = None
        status_code = 500
        route_path = request.url.path
        try:
            response = await call_next(request)
            status_code = response.status_code
            route = request.scope.get("route")
            if route is not None:
                route_path = getattr(route, "path", route_path)
        except Exception as exc:
            logger.error(
                "unhandled exception",
                extra={
                    "event": "api.error",
                    "http": {"method": request.method, "path": route_path},
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                },
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "internal_error", "request_id": request_id},
            )
        finally:
            duration_s = time.perf_counter() - start
            duration_ms = duration_s * 1000.0

            labels = {"method": request.method, "path": route_path, "status": str(status_code)}
            counter_inc(API_REQUESTS_TOTAL, **labels)
            hist_observe(API_REQUEST_DURATION_SECONDS, duration_s, **labels)

            logger.info(
                "request complete",
                extra={
                    "event": "api.request",
                    "http": {
                        "method": request.method,
                        "path": route_path,
                        "status": status_code,
                        "duration_ms": round(duration_ms, 3),
                    },
                },
            )

            set_request_id(prev_request_id)
            set_replay_run_id(prev_replay_run_id)

        if response is None:
            response = JSONResponse(
                status_code=500,
                content={"detail": "internal_error", "request_id": request_id},
            )
        response.headers["X-Request-ID"] = request_id
        return response

    if resolved.enable_metrics:
        @app.get("/metrics", include_in_schema=False)
        def get_metrics() -> Response:
            if generate_latest is None:
                raise HTTPException(status_code=503, detail="prometheus_client_not_installed")
            payload = generate_latest()
            return PlainTextResponse(payload.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

    app.include_router(health.router)

    router = APIRouter(prefix="/api/v1")
    router.include_router(manifests.router)
    router.include_router(diffing.router)
    router.include_router(replay.router)
    router.include_router(lineage.router)
    app.include_router(router)

    return app


app = create_app()
