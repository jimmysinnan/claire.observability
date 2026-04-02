import logging

from elasticsearch import Elasticsearch

from app.core.config import settings

logger = logging.getLogger(__name__)


class LogStore:
    def __init__(self) -> None:
        self.client = Elasticsearch(settings.elasticsearch_url)

    def index_request_log(self, payload: dict) -> None:
        try:
            self.client.index(index="claire-request-logs", document=payload)
        except Exception as exc:  # Best-effort logging
            logger.warning("failed_to_index_request_log", extra={"error": str(exc)})
