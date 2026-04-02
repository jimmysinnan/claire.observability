import logging
import time
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import generate_latest

from app.api.routes import router
from app.core.logging import configure_logging
from app.core.telemetry import configure_telemetry
from app.storage.logs import LogStore
from app.web.routes import router as web_router

configure_logging()
configure_telemetry()
logger = logging.getLogger(__name__)
log_store = LogStore()

app = FastAPI(title="Mira AI Observability", version="0.2.0")
app.include_router(router, prefix="/api/v1", tags=["observability"])
app.include_router(web_router, tags=["web"])
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    start = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start) * 1000, 2)
    payload = {
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "latency_ms": latency_ms,
    }
    logger.info("request_log", extra=payload)
    log_store.index_request_log(payload)
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/prometheus")
async def prometheus_metrics() -> Response:
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")
