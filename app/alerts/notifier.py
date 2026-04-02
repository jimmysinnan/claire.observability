import logging

import httpx

from app.core.config import settings
from app.models.schemas import Anomaly

logger = logging.getLogger(__name__)


class AlertNotifier:
    async def notify(self, anomaly: Anomaly) -> None:
        if settings.slack_webhook_url:
            await self._notify_slack(anomaly)

        if settings.alert_email_recipient:
            logger.info(
                "email_alert_placeholder",
                extra={
                    "recipient": settings.alert_email_recipient,
                    "anomaly": anomaly.model_dump(),
                },
            )

    async def _notify_slack(self, anomaly: Anomaly) -> None:
        async with httpx.AsyncClient(timeout=5) as client:
            payload = {"text": f"[Mira Alert] {anomaly.rule_name}: {anomaly.reason}"}
            response = await client.post(settings.slack_webhook_url, json=payload)
            response.raise_for_status()
