from datetime import datetime

from app.ingestion.normalizer import normalize_event
from app.models.schemas import AIEvent, EventMetadata, EventType


def test_normalize_event_removes_pii_and_extracts_fields() -> None:
    event = AIEvent(
        event_id="evt-1",
        event_type=EventType.recommendation,
        prompt="recommend shoes now",
        context={"email": "a@b.com", "locale": "fr"},
        prediction={
            "recommended_products": [{"product_id": "sku-1", "stock": 0}],
            "proposed_price": 25,
        },
        metadata=EventMetadata(agent_version="1.0.0", timestamp=datetime.utcnow()),
    )

    normalized = normalize_event(event)

    assert normalized.product_ids == ["sku-1"]
    assert normalized.price_candidates == [25.0]
    assert "email" not in normalized.metadata["context"]
