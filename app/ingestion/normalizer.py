from app.models.schemas import AIEvent, NormalizedEvent

PII_KEYS = {"email", "phone", "address", "full_name", "first_name", "last_name"}


def sanitize_context(context: dict) -> dict:
    return {k: v for k, v in context.items() if k.lower() not in PII_KEYS}


def normalize_event(event: AIEvent) -> NormalizedEvent:
    prediction = event.prediction or {}
    recommendations = prediction.get("recommended_products", [])
    proposed_price = prediction.get("proposed_price")

    return NormalizedEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        timestamp=event.metadata.timestamp,
        product_ids=[
            str(item.get("product_id"))
            for item in recommendations
            if item.get("product_id")
        ],
        price_candidates=[float(proposed_price)] if proposed_price is not None else [],
        stock_state={
            str(item.get("product_id")): int(item.get("stock", 0))
            for item in recommendations
            if item.get("product_id")
        },
        prompt_tokens=len(event.prompt.split()),
        metadata={
            "agent_version": event.metadata.agent_version,
            "source": event.metadata.source,
            "context": sanitize_context(event.context),
        },
    )
