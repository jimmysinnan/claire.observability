from datetime import datetime

import pytest

from app.models.schemas import AIEvent, EventMetadata, EventType
from app.services.pipeline import ProcessingPipeline


@pytest.mark.asyncio
async def test_pipeline_records_metrics_and_anomalies() -> None:
    pipeline = ProcessingPipeline()
    event = AIEvent(
        event_id="evt-2",
        event_type=EventType.recommendation,
        prompt="prompt",
        context={"locale": "fr"},
        prediction={
            "recommended_products": [{"product_id": "sku-1", "stock": 0}],
            "proposed_price": -1,
        },
        metadata=EventMetadata(agent_version="1", timestamp=datetime.utcnow()),
    )

    anomalies = await pipeline.process(event)
    snapshot = pipeline.metrics.snapshot()

    assert len(anomalies) >= 2
    assert snapshot.total_events == 1
    assert snapshot.anomalies_detected >= 2
