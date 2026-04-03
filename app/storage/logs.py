import logging
from collections import deque
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback store (last 500 entries)
_memory_store: deque[dict[str, Any]] = deque(maxlen=500)


def _try_elasticsearch() -> Any | None:
    """Attempt to create an Elasticsearch client. Returns None if unavailable."""
    try:
        from elasticsearch import Elasticsearch

        client = Elasticsearch(settings.elasticsearch_url, request_timeout=2)
        client.ping()
        return client
    except Exception:
        return None


class LogStore:
    def __init__(self) -> None:
        self._es = _try_elasticsearch()
        if self._es:
            logger.info("log_store_backend", extra={"backend": "elasticsearch"})
        else:
            logger.info("log_store_backend", extra={"backend": "memory"})

    def index_request_log(self, payload: dict[str, Any]) -> None:
        _memory_store.append(payload)
        if self._es:
            try:
                self._es.index(index="claire-request-logs", document=payload)
            except Exception as exc:
                logger.warning("es_index_failed", extra={"error": str(exc)})

    def recent_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(_memory_store)[-limit:]
