AnomalyRule = Callable[[NormalizedEvent], list[Anomaly]]


class AnomalyEngine:
    def __init__(self, rules: list[AnomalyRule] | None = None) -> None:
        self.rules = rules or [
            detect_negative_price,
            detect_out_of_stock_recommendation,
            detect_hallucination,
        ]

    def detect(self, event: NormalizedEvent) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for rule in self.rules:
            anomalies.extend(rule(event))
        return anomalies
