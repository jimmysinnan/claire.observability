"""
Root Cause Analysis — analyse les anomalies récentes d'un agent
et produit un diagnostic structuré + hypothèses de cause racine.
"""
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.database import engine
from app.models.db_models import AgentDB, AnomalyDB, LogEntryDB


def run_rca(agent_id: str) -> dict:
    """
    Analyse les dernières 24h d'activité d'un agent et retourne un rapport RCA.
    """
    with Session(engine) as session:
        agent = session.get(AgentDB, agent_id)
        if agent is None:
            return {"error": "Agent introuvable"}

        since = datetime.utcnow() - timedelta(hours=24)

        anomalies = session.exec(
            select(AnomalyDB)
            .where(AnomalyDB.agent_id == agent_id)
            .where(AnomalyDB.created_at >= since)
            .order_by(AnomalyDB.created_at.desc())
        ).all()

        recent_logs = session.exec(
            select(LogEntryDB)
            .where(LogEntryDB.agent_id == agent_id)
            .where(LogEntryDB.level.in_(["ERROR", "WARNING"]))
            .where(LogEntryDB.timestamp >= since)
            .order_by(LogEntryDB.timestamp.desc())
            .limit(20)
        ).all()

    # Analyse des patterns
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    rule_counts: dict[str, int] = {}
    for a in anomalies:
        severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
        rule_counts[a.rule_name] = rule_counts.get(a.rule_name, 0) + 1

    top_rule = max(rule_counts, key=lambda k: rule_counts[k]) if rule_counts else None
    error_rate = round(agent.errors_today / agent.runs_today * 100, 1) if agent.runs_today else 0

    # Génération du diagnostic
    hypotheses = _build_hypotheses(agent, anomalies, error_rate, top_rule)
    severity = _overall_severity(severity_counts, error_rate)

    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "integration": agent.integration,
        "analysis_period": "Dernières 24h",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": _build_summary(agent, anomalies, error_rate, severity),
        "severity": severity,
        "metrics": {
            "runs_today": agent.runs_today,
            "errors_today": agent.errors_today,
            "error_rate_pct": error_rate,
            "anomalies_detected": len(anomalies),
            "health_score": agent.health_score,
        },
        "top_anomaly_rule": top_rule,
        "anomaly_breakdown": severity_counts,
        "hypotheses": hypotheses,
        "recommended_playbook": _recommend_playbook(agent.integration, top_rule),
    }


def _overall_severity(counts: dict, error_rate: float) -> str:
    if counts["critical"] > 0 or error_rate > 40:
        return "critical"
    if counts["high"] > 2 or error_rate > 20:
        return "high"
    if counts["medium"] > 3 or error_rate > 10:
        return "medium"
    return "low"


def _build_summary(agent: AgentDB, anomalies: list, error_rate: float, severity: str) -> str:
    if not anomalies and error_rate == 0:
        return (
            f"L'agent '{agent.name}' ne présente aucune anomalie détectée sur les dernières 24h. "
            "Le comportement est dans les normes attendues."
        )
    parts = [f"L'agent '{agent.name}' ({agent.integration}) présente {len(anomalies)} anomalie(s) détectée(s)."]
    if error_rate > 0:
        parts.append(f"Taux d'erreur actuel : {error_rate}% ({agent.errors_today}/{agent.runs_today} runs).")
    parts.append(f"Sévérité globale estimée : {severity.upper()}.")
    return " ".join(parts)


def _build_hypotheses(agent: AgentDB, anomalies: list, error_rate: float, top_rule: str | None) -> list[dict]:
    hypotheses = []
    integration = agent.integration

    # Hypothèse 1 — basée sur le top rule
    if top_rule == "price_anomaly":
        hypotheses.append({
            "rank": 1,
            "confidence": "high",
            "hypothesis": "Dérive du modèle de pricing",
            "detail": "Le moteur de recommandation produit des prix hors des bornes configurées. Vérifiez les paramètres min/max prix et la fraîcheur des données de catalogue.",
        })
    elif top_rule == "hallucination_risk":
        hypotheses.append({
            "rank": 1,
            "confidence": "high",
            "hypothesis": "Hallucinations LLM détectées",
            "detail": "Le modèle génère du contenu non ancré dans le contexte fourni. Réduire la température, augmenter le grounding RAG, ou limiter le scope des outils disponibles.",
        })
    elif top_rule == "latency_spike":
        hypotheses.append({
            "rank": 1,
            "confidence": "medium",
            "hypothesis": "Dégradation des performances",
            "detail": "Les temps de réponse dépassent les seuils normaux. Cause probable : saturation API tierce, payload trop large, ou boucle d'outils non terminée.",
        })
    elif top_rule:
        hypotheses.append({
            "rank": 1,
            "confidence": "medium",
            "hypothesis": f"Règle '{top_rule}' déclenchée de façon répétée",
            "detail": "Un pattern récurrent correspond à cette règle. Analysez les inputs déclencheurs pour identifier un changement upstream.",
        })

    # Hypothèse 2 — basée sur l'intégration
    if integration == "make":
        hypotheses.append({
            "rank": len(hypotheses) + 1,
            "confidence": "medium",
            "hypothesis": "Rupture de scénario Make",
            "detail": "Un module Make a peut-être atteint sa limite d'opérations ou une connexion a expiré. Vérifiez le journal d'exécution dans Make Dashboard.",
        })
    elif integration == "n8n":
        hypotheses.append({
            "rank": len(hypotheses) + 1,
            "confidence": "medium",
            "hypothesis": "Nœud n8n en erreur silencieuse",
            "detail": "Un nœud du workflow n8n peut échouer sans interrompre l'exécution. Activez les logs d'exécution détaillés dans n8n et vérifiez chaque nœud.",
        })
    elif integration in ("claude", "openai", "gemini"):
        hypotheses.append({
            "rank": len(hypotheses) + 1,
            "confidence": "low",
            "hypothesis": "Changement de comportement du modèle",
            "detail": "Une mise à jour silencieuse du modèle LLM peut modifier les outputs. Comparez les réponses avec une version pinned ou un snapshot de référence.",
        })

    # Hypothèse générique si taux d'erreur élevé
    if error_rate > 20:
        hypotheses.append({
            "rank": len(hypotheses) + 1,
            "confidence": "medium",
            "hypothesis": "Volume de données d'entrée anormal",
            "detail": f"Avec {error_rate}% de taux d'erreur, un changement dans les données entrantes est probable. Comparez la distribution des inputs des dernières 24h avec la baseline.",
        })

    if not hypotheses:
        hypotheses.append({
            "rank": 1,
            "confidence": "low",
            "hypothesis": "Anomalie transitoire",
            "detail": "Aucun pattern fort identifié. L'anomalie est probablement transitoire. Surveillez sur 1h supplémentaire avant d'intervenir.",
        })

    return hypotheses


def _recommend_playbook(integration: str, top_rule: str | None) -> str:
    mapping = {
        ("make", "latency_spike"): "make-performance",
        ("make", None): "make-general",
        ("n8n", "latency_spike"): "n8n-performance",
        ("n8n", None): "n8n-general",
        ("claude", "hallucination_risk"): "llm-hallucination",
        ("openai", "hallucination_risk"): "llm-hallucination",
        ("gemini", "hallucination_risk"): "llm-hallucination",
        (None, "price_anomaly"): "pricing-drift",
    }
    key = (integration, top_rule)
    if key in mapping:
        return mapping[key]
    # Fallback par intégration
    fallback = {
        "make": "make-general",
        "n8n": "n8n-general",
        "claude": "llm-general",
        "openai": "llm-general",
        "gemini": "llm-general",
    }
    return fallback.get(integration, "general-recovery")
