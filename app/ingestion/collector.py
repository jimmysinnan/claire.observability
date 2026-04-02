import json
import logging

from aiokafka import AIOKafkaProducer

from app.core.config import settings
from app.models.schemas import AIEvent

logger = logging.getLogger(__name__)


class EventCollector:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def publish(self, event: AIEvent) -> None:
        if not self._producer:
            raise RuntimeError("Collector not started")
        await self._producer.send_and_wait(
            settings.kafka_events_topic,
            json.dumps(event.model_dump(mode="json")).encode("utf-8"),
        )
        logger.info("event_published", extra={"event_id": event.event_id})
