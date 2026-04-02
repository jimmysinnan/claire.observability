from collections import Counter

from prometheus_client import Counter as PromCounter

from app.models.schemas import Anomaly, MetricsSnapshot

EVENT_COUNTER = PromCounter("claire_events_total", "Total ingested AI events")
ANOMALY_COUNTER = PromCounter("claire_anomalies_total", "Total anomalies", ["rule_name"])


class MetricsStore:
    def __init__(self) -> None:
        self.total_events = 0
        self.anomalies = Counter()

    def record_event(self) -> None:
        self.total_events += 1
        EVENT_COUNTER.inc()

    def record_anomalies(self, anomalies: list[Anomaly]) -> None:
        for anomaly in anomalies:
            self.anomalies[anomaly.rule_name] += 1
            ANOMALY_COUNTER.labels(anomaly.rule_name).inc()

    def snapshot(self) -> MetricsSnapshot:
        return MetricsSnapshot(
            total_events=self.total_events,
            anomalies_detected=sum(self.anomalies.values()),
            anomalies_by_rule=dict(self.anomalies),
        )
