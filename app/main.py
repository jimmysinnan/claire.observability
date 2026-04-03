import logging
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import generate_latest

from app.agents.registry import emit_log, _seed_demo_agents
from app.api.routes import router
from app.core.logging import configure_logging
from app.core.telemetry import configure_telemetry
from app.integrations.manager import init_integrations
from app.models.schemas import LogLevel
from app.storage.logs import LogStore
from app.web.routes import router as web_router

configure_logging()
configure_telemetry()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    init_integrations()
    _seed_demo_agents()
    emit_log("Claire Observability démarrée", level=LogLevel.success, source="system")
    yield
    # Shutdown
    emit_log("Claire Observability arrêtée", level=LogLevel.warning, source="system")


app = FastAPI(title="Claire AI Observability", version="1.0.0", lifespan=lifespan)
app.include_router(router, prefix="/api/v1", tags=["api"])
app.include_router(web_router, tags=["web"])
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

log_store = LogStore()


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    start = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start) * 1000, 2)
    # Skip noise for static assets and health checks
    if not request.url.path.startswith("/static") and request.url.path != "/health":
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
    return {"status": "ok", "version": "1.0.0"}


@app.get("/prometheus")
async def prometheus_metrics() -> Response:
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")
