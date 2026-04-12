"""
Playbooks — bibliothèque de procédures de remédiation par type d'intégration et d'anomalie.
Chaque playbook est une liste d'étapes actionnables depuis l'UI.
"""
from typing import Any

PLAYBOOKS: dict[str, dict[str, Any]] = {
    "make-general": {
        "id": "make-general",
        "title": "Remédiation Make — Général",
        "description": "Procédure standard pour diagnostiquer et relancer un scénario Make défaillant.",
        "estimated_minutes": 10,
        "steps": [
            {"id": "s1", "order": 1, "title": "Vérifier le journal Make", "description": "Ouvrir le tableau de bord Make et inspecter le dernier run du scénario. Identifier le module en erreur.", "action": None, "status": "pending"},
            {"id": "s2", "order": 2, "title": "Contrôler les connexions", "description": "S'assurer que les connexions OAuth/API du scénario sont actives et non expirées.", "action": "check_connections", "status": "pending"},
            {"id": "s3", "order": 3, "title": "Throttler à 50%", "description": "Réduire la cadence d'exécution pour éviter les rate limits pendant le diagnostic.", "action": "throttle_50", "status": "pending"},
            {"id": "s4", "order": 4, "title": "Relancer un run test", "description": "Déclencher manuellement le scénario avec un payload test pour valider la reprise.", "action": "trigger_test_run", "status": "pending"},
            {"id": "s5", "order": 5, "title": "Rétablir le débit normal", "description": "Si le test est concluant, remettre le throttle à 100%.", "action": "throttle_100", "status": "pending"},
        ],
    },
    "make-performance": {
        "id": "make-performance",
        "title": "Remédiation Make — Latence élevée",
        "description": "Procédure pour résoudre les pics de latence dans un scénario Make.",
        "estimated_minutes": 15,
        "steps": [
            {"id": "s1", "order": 1, "title": "Identifier le module lent", "description": "Dans le journal d'exécution Make, repérer le module qui consomme le plus de temps.", "action": None, "status": "pending"},
            {"id": "s2", "order": 2, "title": "Réduire la taille des payloads", "description": "Limiter les champs retournés par les modules API (projection/filtering).", "action": None, "status": "pending"},
            {"id": "s3", "order": 3, "title": "Activer le mode synchrone", "description": "Passer l'exécution en synchrone pour limiter les timeouts en cascade.", "action": "enable_sync_mode", "status": "pending"},
            {"id": "s4", "order": 4, "title": "Vérifier les quotas API", "description": "Contrôler les limites de l'API tierce connectée (rate limit, quota journalier).", "action": None, "status": "pending"},
            {"id": "s5", "order": 5, "title": "Valider la stabilisation", "description": "Observer 10 runs consécutifs — la latence doit revenir sous 2s.", "action": None, "status": "pending"},
        ],
    },
    "n8n-general": {
        "id": "n8n-general",
        "title": "Remédiation n8n — Général",
        "description": "Procédure standard pour diagnostiquer et relancer un workflow n8n défaillant.",
        "estimated_minutes": 10,
        "steps": [
            {"id": "s1", "order": 1, "title": "Activer les logs détaillés", "description": "Dans n8n > Settings > Log Level, passer en 'debug' temporairement.", "action": None, "status": "pending"},
            {"id": "s2", "order": 2, "title": "Identifier le nœud défaillant", "description": "Inspecter l'exécution la plus récente dans n8n > Executions. Le nœud rouge est la source.", "action": None, "status": "pending"},
            {"id": "s3", "order": 3, "title": "Tester le nœud isolément", "description": "Exécuter uniquement le nœud problématique avec un input statique pour confirmer l'erreur.", "action": None, "status": "pending"},
            {"id": "s4", "order": 4, "title": "Vérifier les credentials", "description": "S'assurer que les credentials du nœud sont valides et non expirés.", "action": "check_credentials", "status": "pending"},
            {"id": "s5", "order": 5, "title": "Redémarrer le workflow", "description": "Désactiver puis réactiver le workflow n8n pour forcer la reprise propre.", "action": "restart_workflow", "status": "pending"},
        ],
    },
    "n8n-performance": {
        "id": "n8n-performance",
        "title": "Remédiation n8n — Performance",
        "description": "Procédure pour optimiser les performances d'un workflow n8n.",
        "estimated_minutes": 20,
        "steps": [
            {"id": "s1", "order": 1, "title": "Profiler l'exécution", "description": "Analyser les temps d'exécution par nœud dans le panel Executions.", "action": None, "status": "pending"},
            {"id": "s2", "order": 2, "title": "Limiter les batch sizes", "description": "Réduire le nombre d'items traités par batch dans les nœuds Loop/SplitInBatches.", "action": None, "status": "pending"},
            {"id": "s3", "order": 3, "title": "Ajouter un Wait node", "description": "Insérer un nœud Wait de 500ms après les appels API intensifs pour éviter le rate limiting.", "action": None, "status": "pending"},
            {"id": "s4", "order": 4, "title": "Activer le throttling agent", "description": "Réduire la fréquence d'exécution du workflow à 50% le temps du diagnostic.", "action": "throttle_50", "status": "pending"},
            {"id": "s5", "order": 5, "title": "Valider sur 5 exécutions", "description": "Observer 5 runs — tous doivent passer sous 5s.", "action": None, "status": "pending"},
        ],
    },
    "llm-hallucination": {
        "id": "llm-hallucination",
        "title": "Remédiation LLM — Hallucinations",
        "description": "Procédure pour réduire les hallucinations dans un agent LLM.",
        "estimated_minutes": 30,
        "steps": [
            {"id": "s1", "order": 1, "title": "Mettre l'agent en pause", "description": "Stopper immédiatement les exécutions actives pour éviter de propager des outputs incorrects.", "action": "pause_agent", "status": "pending"},
            {"id": "s2", "order": 2, "title": "Analyser les outputs récents", "description": "Examiner les 10 derniers outputs de l'agent et identifier les patterns hallucinatoires.", "action": None, "status": "pending"},
            {"id": "s3", "order": 3, "title": "Ajuster le system prompt", "description": "Renforcer les instructions de grounding : 'Réponds uniquement en te basant sur le contexte fourni.'", "action": None, "status": "pending"},
            {"id": "s4", "order": 4, "title": "Réduire la température", "description": "Baisser la température LLM à 0.1–0.3 pour des réponses plus déterministes.", "action": None, "status": "pending"},
            {"id": "s5", "order": 5, "title": "Activer les guardrails faithfulness", "description": "Activer la vérification de faithfulness dans les guardrails Claire.", "action": "enable_faithfulness_guardrail", "status": "pending"},
            {"id": "s6", "order": 6, "title": "Relancer en mode supervisé", "description": "Remettre l'agent en run avec monitoring renforcé pendant 30 minutes.", "action": "resume_agent", "status": "pending"},
        ],
    },
    "llm-general": {
        "id": "llm-general",
        "title": "Remédiation LLM — Général",
        "description": "Procédure générique pour diagnostiquer un agent LLM en erreur.",
        "estimated_minutes": 15,
        "steps": [
            {"id": "s1", "order": 1, "title": "Vérifier le statut de l'API", "description": "Consulter la page de statut du provider LLM (status.anthropic.com, status.openai.com).", "action": None, "status": "pending"},
            {"id": "s2", "order": 2, "title": "Contrôler les quotas", "description": "Vérifier que la clé API n'a pas atteint sa limite de tokens ou de requêtes.", "action": "check_api_quota", "status": "pending"},
            {"id": "s3", "order": 3, "title": "Tester avec un prompt simple", "description": "Envoyer un prompt minimal à l'API pour confirmer que l'accès fonctionne.", "action": "test_ping", "status": "pending"},
            {"id": "s4", "order": 4, "title": "Rollback configuration", "description": "Revenir à la dernière configuration stable de l'agent.", "action": "rollback", "status": "pending"},
            {"id": "s5", "order": 5, "title": "Reprendre le monitoring", "description": "Relancer l'agent et surveiller les 5 prochaines exécutions.", "action": "resume_agent", "status": "pending"},
        ],
    },
    "pricing-drift": {
        "id": "pricing-drift",
        "title": "Remédiation — Dérive de pricing",
        "description": "Procédure pour corriger un agent de pricing qui sort des bornes autorisées.",
        "estimated_minutes": 20,
        "steps": [
            {"id": "s1", "order": 1, "title": "Mettre l'agent en pause", "description": "Suspendre immédiatement pour éviter des prix aberrants en production.", "action": "pause_agent", "status": "pending"},
            {"id": "s2", "order": 2, "title": "Auditer les derniers prix générés", "description": "Extraire les outputs de pricing des 2 dernières heures et comparer aux règles métier.", "action": None, "status": "pending"},
            {"id": "s3", "order": 3, "title": "Vérifier les bornes configurées", "description": "Confirmer que les contraintes min/max prix sont correctement appliquées dans le prompt ou les règles.", "action": None, "status": "pending"},
            {"id": "s4", "order": 4, "title": "Rollback à la config précédente", "description": "Restaurer la configuration de l'agent avant le dernier changement.", "action": "rollback", "status": "pending"},
            {"id": "s5", "order": 5, "title": "Reprendre avec throttle 25%", "description": "Relancer à 25% de débit pour valider les prix sur un échantillon réduit.", "action": "throttle_25", "status": "pending"},
            {"id": "s6", "order": 6, "title": "Valider et rétablir le débit", "description": "Après validation manuelle de 10 prix, remettre à 100%.", "action": "throttle_100", "status": "pending"},
        ],
    },
    "general-recovery": {
        "id": "general-recovery",
        "title": "Remédiation générale",
        "description": "Procédure de reprise générique applicable à tout type d'agent.",
        "estimated_minutes": 10,
        "steps": [
            {"id": "s1", "order": 1, "title": "Mettre l'agent en pause", "description": "Suspendre l'agent pour interrompre les erreurs en cascade.", "action": "pause_agent", "status": "pending"},
            {"id": "s2", "order": 2, "title": "Consulter les logs récents", "description": "Examiner les 20 dernières entrées de log pour identifier le premier signal d'erreur.", "action": None, "status": "pending"},
            {"id": "s3", "order": 3, "title": "Rollback configuration", "description": "Revenir à la dernière configuration stable connue.", "action": "rollback", "status": "pending"},
            {"id": "s4", "order": 4, "title": "Relancer en mode limité", "description": "Reprendre l'agent à 25% de débit.", "action": "throttle_25", "status": "pending"},
            {"id": "s5", "order": 5, "title": "Rétablir le débit normal", "description": "Si les 5 premiers runs sont OK, remettre à 100%.", "action": "throttle_100", "status": "pending"},
        ],
    },
}


def get_playbook(playbook_id: str) -> dict | None:
    return PLAYBOOKS.get(playbook_id)


def list_playbooks_for_agent(integration: str, recommended_id: str | None = None) -> list[dict]:
    """Retourne les playbooks pertinents pour une intégration donnée."""
    integration_map = {
        "make": ["make-general", "make-performance"],
        "n8n": ["n8n-general", "n8n-performance"],
        "claude": ["llm-hallucination", "llm-general"],
        "openai": ["llm-hallucination", "llm-general"],
        "gemini": ["llm-hallucination", "llm-general"],
        "custom": ["general-recovery"],
    }
    ids = integration_map.get(integration, ["general-recovery"])

    # S'assurer que le playbook recommandé est en tête
    if recommended_id and recommended_id not in ids:
        ids = [recommended_id] + ids
    elif recommended_id and recommended_id in ids:
        ids = [recommended_id] + [i for i in ids if i != recommended_id]

    result = []
    for pid in ids:
        pb = PLAYBOOKS.get(pid)
        if pb:
            result.append({
                "id": pb["id"],
                "title": pb["title"],
                "description": pb["description"],
                "estimated_minutes": pb["estimated_minutes"],
                "step_count": len(pb["steps"]),
                "recommended": pid == recommended_id,
            })
    return result


def apply_step(playbook_id: str, step_id: str, agent_id: str) -> dict:
    """
    Simule l'application d'une étape de playbook.
    En production, les actions string mapperaient vers des fonctions réelles.
    """
    pb = PLAYBOOKS.get(playbook_id)
    if not pb:
        return {"success": False, "error": "Playbook introuvable"}

    step = next((s for s in pb["steps"] if s["id"] == step_id), None)
    if not step:
        return {"success": False, "error": "Étape introuvable"}

    action = step.get("action")
    message = f"Étape '{step['title']}' marquée comme effectuée."
    if action:
        message = f"Action '{action}' déclenchée pour l'agent {agent_id}."

    return {
        "success": True,
        "playbook_id": playbook_id,
        "step_id": step_id,
        "action": action,
        "message": message,
    }
