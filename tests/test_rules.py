from datetime import datetime

from app.anomalies.rules import (
    detect_hallucination,
    detect_negative_price,
    detect_out_of_stock_recommendation,
)
from app.models.schemas import EventType, NormalizedEvent


def build_event() -> NormalizedEvent:
    return NormalizedEvent(
        event_id="evt-1",
        event_type=EventType.recommendation,
        timestamp=datetime.utcnow(),
        product_ids=["sku-1"],
        price_candidates=[-1.0],
        stock_state={"sku-1": 0},
        metadata={"context": {"claim": "100% guaranteed and unverified"}},
    )


def test_rules_detect_expected_anomalies() -> None:
    event = build_event()
    assert detect_negative_price(event)
    assert detect_out_of_stock_recommendation(event)
    assert detect_hallucination(event)
