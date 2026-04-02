from fastapi import APIRouter, Depends

from app.core.auth import token_dependency
from app.models.schemas import AIEvent, Anomaly, MetricsSnapshot
from app.services.pipeline import ProcessingPipeline

router = APIRouter()
pipeline = ProcessingPipeline()


@router.post("/events", dependencies=[Depends(token_dependency)])
async def ingest_event(event: AIEvent) -> dict:
    anomalies = await pipeline.process(event)
    return {"event_id": event.event_id, "anomalies": [a.model_dump(mode="json") for a in anomalies]}


@router.get("/anomalies", response_model=list[Anomaly], dependencies=[Depends(token_dependency)])
async def list_anomalies() -> list[Anomaly]:
    return pipeline.anomaly_store


@router.get("/metrics", response_model=MetricsSnapshot, dependencies=[Depends(token_dependency)])
async def metrics_snapshot() -> MetricsSnapshot:
    return pipeline.metrics.snapshot()
