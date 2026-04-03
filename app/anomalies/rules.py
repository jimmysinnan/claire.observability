import uuid
from collections.abc import Callable

from app.anomalies.classifier import hallucination_classifier
from app.models.schemas import Anomaly, NormalizedEvent, Severity

AnomalyRule = Callable[[NormalizedEvent], list[Anomaly]]


def detect_negative_price(event: NormalizedEvent) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    for price in event.price_candidates:
        if price < 0:
            anomalies.append(
                Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    event_id=event.event_id,
                    rule_name="negative_price",
                    severity=Severity.high,
                    reason=f"Prix négatif détecté : {price}",
                )
            )
    return anomalies


def detect_out_of_stock_recommendation(event: NormalizedEvent) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    for product_id, stock in event.stock_state.items():
        if stock == 0 and product_id in event.product_ids:
            anomalies.append(
                Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    event_id=event.event_id,
                    rule_name="out_of_stock_recommendation",
                    severity=Severity.medium,
                    reason=f"Produit {product_id} recommandé mais en rupture de stock",
                )
            )
    return anomalies


def detect_hallucination(event: NormalizedEvent) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    context_text = " ".join(str(v) for v in event.metadata.get("context", {}).values())
    if hallucination_classifier(context_text):
        anomalies.append(
            Anomaly(
                anomaly_id=str(uuid.uuid4()),
                event_id=event.event_id,
                rule_name="hallucination_markers",
                severity=Severity.low,
                reason="Marqueurs de langage suspects détectés dans le contexte",
            )
        )
    return anomalies
