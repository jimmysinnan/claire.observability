# Claire
Observability IA
# Mira — Outil d'observabilité IA e-commerce (MVP)

Ce dépôt fournit un MVP modulaire d'observabilité IA e-commerce avec une expérience web orientée conversion inspirée des parcours produits de plateformes data reliability enterprise.

## 1) Architecture

### Modules
- **Collecteur d'événements** (`app/ingestion/collector.py`) : publication d'événements bruts vers Kafka.
- **Normalisateur** (`app/ingestion/normalizer.py`) : harmonisation des champs et suppression de PII non nécessaire (RGPD).
- **Moteur d'anomalies** (`app/anomalies/engine.py`, `app/anomalies/rules.py`) : règles de détection + extension plug-in ML.
- **API REST & SDK** (`app/main.py`, `app/api/routes.py`, `app/sdk/*`) : ingestion, consultation anomalies/métriques, instrumentation client.
- **Couche stockage** :
  - métriques en mémoire + export Prometheus (`app/storage/metrics.py`),
  - logs requêtes Elasticsearch (`app/storage/logs.py`),
  - configuration InfluxDB prête.
- **Web App UX (conversion + dashboard)** (`app/web/*`) :
  - landing page premium,
  - product tour,
  - funnel de conversion `/demo`,
  - dashboard de fiabilité `/dashboard`.

### Flux inter-modules
- **Kafka topics**
  - `ai.events.raw` : événements entrants.
  - `ai.events.normalized` : événements normalisés (extension worker).
  - `ai.events.anomalies` : anomalies détectées (extension worker).
- **REST endpoints**
  - `POST /api/v1/events` : ingérer prompt, contexte, prédiction, métadonnées.
  - `GET /api/v1/anomalies` : consulter anomalies.
  - `GET /api/v1/metrics` : snapshot métriques métier.
  - `GET /prometheus` : exposition métriques scrapeables.
- **Web routes (UX/UI)**
  - `GET /` : landing + CTA.
  - `GET /tour` : parcours produit.
  - `GET/POST /demo` : capture lead.
  - `GET /dashboard` : pilotage opérationnel.

## 2) Schémas de données

### Event
```json
{
  "event_id": "evt-1",
  "event_type": "recommendation",
  "prompt": "Suggest shoes",
  "context": {"locale": "fr-FR"},
  "prediction": {
    "recommended_products": [{"product_id": "sku-1", "stock": 0}],
    "proposed_price": 19.99
  },
  "metadata": {
    "user_id_hash": "sha256:...",
    "session_id": "sess-1",
    "agent_version": "v1.2.0",
    "source": "agent",
    "timestamp": "2026-01-01T10:00:00Z"
  }
}
```

### Anomaly
```json
{
  "anomaly_id": "evt-1-oos-sku-1",
  "event_id": "evt-1",
  "rule_name": "out_of_stock_recommendation",
  "severity": "medium",
  "reason": "Product sku-1 recommended while out of stock",
  "created_at": "2026-01-01T10:00:00Z",
  "metadata": {}
}
```

## 3) Détection d'anomalies (règles MVP)
- Prix négatif (`negative_price`).
- Produit hors stock recommandé (`out_of_stock_recommendation`).
- Hallucination suspecte via classificateur baseline (`hallucination_detected`).

## 4) Sécurité, gouvernance et RGPD
- Authentification API via `X-API-Token`.
- Journalisation des requêtes HTTP en JSON + indexation Elasticsearch.
- Instrumentation OpenTelemetry (OTLP).
- Données personnelles minimisées : `user_id_hash` uniquement, nettoyage des champs sensibles en normalisation.

## 5) Démarrage local
```bash
docker compose up --build
```

- App/API: `http://localhost:8000`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

## 6) Tests & qualité
```bash
python -m pip install -e .[dev]
ruff check .
pytest
```

## 7) Extensibilité
Le moteur d'anomalies accepte des règles injectées :
```python
from app.anomalies.engine import AnomalyEngine

engine = AnomalyEngine(rules=[...])
```
