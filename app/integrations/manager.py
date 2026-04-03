"""
IntegrationManager — gère les connexions aux outils externes (n8n, Make, Claude, etc.).
Chaque intégration expose :
  - un webhook pour recevoir des événements entrants
  - un statut de connexion
  - des métriques d'utilisation
"""
import logging
import uuid
from datetime import datetime

from app.agents.registry import emit_log
from app.models.schemas import (
    Integration,
    IntegrationSource,
    IntegrationStatus,
    LogLevel,
)

logger = logging.getLogger(__name__)

_integrations: dict[str, Integration] = {}


def _default_integrations() -> list[Integration]:
    return [
        Integration(
            integration_id=str(uuid.uuid4()),
            source=IntegrationSource.n8n,
            name="n8n",
            description="Automatisation de workflows open-source. Connectez vos workflows n8n pour observer chaque exécution.",
            webhook_url=None,
            status=IntegrationStatus.disconnected,
        ),
        Integration(
            integration_id=str(uuid.uuid4()),
            source=IntegrationSource.make,
            name="Make (ex-Integromat)",
            description="Plateforme cloud d'automatisation visuelle. Surveillez vos scénarios Make en temps réel.",
            webhook_url=None,
            status=IntegrationStatus.disconnected,
        ),
        Integration(
            integration_id=str(uuid.uuid4()),
            source=IntegrationSource.claude,
            name="Claude (Anthropic)",
            description="Observez les appels à l'API Claude — prompts, tokens, latence, anomalies.",
            webhook_url=None,
            status=IntegrationStatus.disconnected,
        ),
        Integration(
            integration_id=str(uuid.uuid4()),
            source=IntegrationSource.openai,
            name="ChatGPT / OpenAI",
            description="Monitorer les appels OpenAI (GPT-4, GPT-4o...) — coût, latence, erreurs.",
            webhook_url=None,
            status=IntegrationStatus.disconnected,
        ),
        Integration(
            integration_id=str(uuid.uuid4()),
            source=IntegrationSource.gemini,
            name="Gemini (Google)",
            description="Suivez les appels Gemini — tokens, modèles, performances.",
            webhook_url=None,
            status=IntegrationStatus.disconnected,
        ),
        Integration(
            integration_id=str(uuid.uuid4()),
            source=IntegrationSource.custom,
            name="API personnalisée",
            description="Intégrez n'importe quel outil via notre API REST ou webhook générique.",
            webhook_url=None,
            status=IntegrationStatus.disconnected,
        ),
    ]


def init_integrations() -> None:
    for integration in _default_integrations():
        _integrations[integration.integration_id] = integration


def list_integrations() -> list[Integration]:
    return list(_integrations.values())


def get_integration(integration_id: str) -> Integration | None:
    return _integrations.get(integration_id)


def get_integration_by_source(source: IntegrationSource) -> Integration | None:
    for integ in _integrations.values():
        if integ.source == source:
            return integ
    return None


def connect_integration(integration_id: str, api_key: str | None = None) -> Integration | None:
    integ = _integrations.get(integration_id)
    if not integ:
        return None
    integ.api_key_set = bool(api_key)
    integ.status = IntegrationStatus.connected
    # Génère un webhook URL unique pour cette intégration
    integ.webhook_url = f"/api/v1/webhook/{integ.source.value}/{integration_id[:8]}"
    emit_log(
        f"Intégration '{integ.name}' connectée",
        level=LogLevel.success,
        source="integrations",
        integration=integ.source,
    )
    return integ


def disconnect_integration(integration_id: str) -> Integration | None:
    integ = _integrations.get(integration_id)
    if not integ:
        return None
    integ.status = IntegrationStatus.disconnected
    integ.api_key_set = False
    integ.webhook_url = None
    emit_log(
        f"Intégration '{integ.name}' déconnectée",
        level=LogLevel.warning,
        source="integrations",
        integration=integ.source,
    )
    return integ


def record_integration_event(source: IntegrationSource) -> None:
    integ = get_integration_by_source(source)
    if integ:
        integ.events_total += 1
        integ.last_event_at = datetime.utcnow()
