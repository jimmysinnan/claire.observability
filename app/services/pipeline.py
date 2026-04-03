from app.alerts.notifier import AlertNotifier
from app.anomalies.engine import AnomalyEngine  # noqa: F401 — canonical import path
from app.ingestion.normalizer import normalize_event
from app.models.schemas import AIEvent, Anomaly
from app.storage.metrics import MetricsStore


class ProcessingPipeline:
    def __init__(
        self,
        engine: AnomalyEngine | None = None,
        metrics: MetricsStore | None = None,
        notifier: AlertNotifier | None = None,
    ) -> None:
        self.engine = engine or AnomalyEngine()
        self.metrics = metrics or MetricsStore()
        self.notifier = notifier or AlertNotifier()
        self.anomaly_store: list[Anomaly] = []

    async def process(self, event: AIEvent) -> list[Anomaly]:
        self.metrics.record_event()
        normalized = normalize_event(event)
        anomalies = self.engine.detect(normalized)
        self.metrics.record_anomalies(anomalies)
        self.anomaly_store.extend(anomalies)

        for anomaly in anomalies:
            await self.notifier.notify(anomaly)

        return anomalies
