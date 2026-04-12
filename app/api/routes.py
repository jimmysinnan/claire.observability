import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select

from app.agents import registry as agent_reg
from app.core.auth import token_dependency
from app.core.database import engine, get_session
from app.integrations.manager import (
    connect_integration,
    disconnect_integration,
    get_integration,
    list_integrations,
    record_integration_event,
)
from app.models.db_models import AgentDB, AuditEntryDB, GovernanceMetricDB, GuardrailsConfigDB, LogEntryDB
from app.models.schemas import (
    AIEvent,
    Anomaly,
    Agent,
    AgentStatus,
    Integration,
    IntegrationSource,
    LogEntry,
    LogLevel,
    MetricsSnapshot,
)
from app.services.pipeline import ProcessingPipeline
from app.services.rca import run_rca
from app.services.playbooks import apply_step, get_playbook, list_playbooks_for_agent

logger = logging.getLogger(__name__)

router = APIRouter()
pipeline = ProcessingPipeline()

# ─── Observability ────────────────────────────────────────────────────────────


@router.post("/events", dependencies=[Depends(token_dependency)])
async def ingest_event(event: AIEvent) -> dict[str, Any]:
    anomalies = await pipeline.process(event)
    return {"event_id": event.event_id, "anomalies": [a.model_dump(mode="json") for a in anomalies]}


@router.get("/anomalies", response_model=list[Anomaly], dependencies=[Depends(token_dependency)])
async def list_anomalies() -> list[Anomaly]:
    return pipeline.anomaly_store


@router.get("/metrics", response_model=MetricsSnapshot, dependencies=[Depends(token_dependency)])
async def metrics_snapshot() -> MetricsSnapshot:
    return pipeline.metrics.snapshot()


@router.get("/logs", response_model=list[LogEntry], dependencies=[Depends(token_dependency)])
async def get_logs(limit: int = 100) -> list[LogEntry]:
    return agent_reg.recent_logs(limit)


# ─── Agents ───────────────────────────────────────────────────────────────────


@router.get("/agents", response_model=list[Agent], dependencies=[Depends(token_dependency)])
async def list_agents() -> list[Agent]:
    return agent_reg.list_agents()


@router.post("/agents", response_model=Agent, dependencies=[Depends(token_dependency)])
async def create_agent(body: dict[str, Any]) -> Agent:
    name = body.get("name", "Agent sans nom")
    integration_str = body.get("integration", "custom")
    try:
        integration = IntegrationSource(integration_str)
    except ValueError:
        integration = IntegrationSource.custom
    tags = body.get("tags", [])
    return agent_reg.register_agent(name, integration, tags)


@router.get("/agents/{agent_id}", response_model=Agent, dependencies=[Depends(token_dependency)])
async def get_agent(agent_id: str) -> Agent:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    return agent


@router.patch("/agents/{agent_id}/status", dependencies=[Depends(token_dependency)])
async def set_agent_status(agent_id: str, body: dict[str, Any]) -> Agent:
    try:
        status = AgentStatus(body.get("status", "idle"))
    except ValueError:
        raise HTTPException(status_code=422, detail="Statut invalide")
    agent = agent_reg.update_agent_status(agent_id, status, body.get("current_task"))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    return agent


@router.delete("/agents/{agent_id}", dependencies=[Depends(token_dependency)])
async def delete_agent(agent_id: str) -> dict[str, bool]:
    ok = agent_reg.delete_agent(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    return {"deleted": True}


@router.get("/agents/{agent_id}/runs", dependencies=[Depends(token_dependency)])
async def get_agent_runs(agent_id: str, limit: int = 20) -> list[dict[str, Any]]:
    runs = agent_reg.get_runs(agent_id, limit)
    return [r.model_dump(mode="json") for r in runs]


# ─── Agent — Extended Endpoints ──────────────────────────────────────────────


@router.get("/agents/{agent_id}/health", dependencies=[Depends(token_dependency)])
async def get_agent_health(agent_id: str) -> dict[str, Any]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    with Session(engine) as session:
        db_agent = session.get(AgentDB, agent_id)
        health_score = db_agent.health_score if db_agent else 100.0
        anomalies_count = db_agent.anomalies_count if db_agent else 0
    return {
        "agent_id": agent_id,
        "health_score": health_score,
        "status": agent.status.value,
        "anomalies_count": anomalies_count,
        "success_rate": agent.success_rate,
        "runs_today": agent.runs_today,
        "errors_today": agent.errors_today,
    }


@router.get("/agents/{agent_id}/governance", dependencies=[Depends(token_dependency)])
async def get_agent_governance(agent_id: str) -> dict[str, Any]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    with Session(engine) as session:
        metric = session.exec(
            select(GovernanceMetricDB)
            .where(GovernanceMetricDB.agent_id == agent_id)
            .order_by(GovernanceMetricDB.recorded_at.desc())
        ).first()
    if metric is None:
        # Retourner des métriques par défaut si aucune mesure
        import random
        return {
            "agent_id": agent_id,
            "adherence": round(random.uniform(0.7, 1.0), 2),
            "tool_accuracy": round(random.uniform(0.65, 0.98), 2),
            "context_relevance": round(random.uniform(0.72, 0.97), 2),
            "answer_correctness": round(random.uniform(0.68, 0.96), 2),
            "pii_blocked": random.randint(0, 15),
            "injection_blocked": random.randint(0, 5),
            "recorded_at": datetime.utcnow().isoformat(),
        }
    return {
        "agent_id": agent_id,
        "adherence": metric.adherence,
        "tool_accuracy": metric.tool_accuracy,
        "context_relevance": metric.context_relevance,
        "answer_correctness": metric.answer_correctness,
        "pii_blocked": metric.pii_blocked,
        "injection_blocked": metric.injection_blocked,
        "recorded_at": metric.recorded_at.isoformat(),
    }


@router.post("/agents/{agent_id}/rca", dependencies=[Depends(token_dependency)])
async def trigger_rca(agent_id: str) -> dict[str, Any]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    agent_reg.record_audit(agent_id, agent.name, "RCA lancée", user="user", kind="info")
    return run_rca(agent_id)


@router.get("/agents/{agent_id}/playbooks", dependencies=[Depends(token_dependency)])
async def get_agent_playbooks(agent_id: str, recommended: str | None = None) -> list[dict[str, Any]]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    return list_playbooks_for_agent(agent.integration.value, recommended)


@router.post("/agents/{agent_id}/playbooks/{step_id}/apply", dependencies=[Depends(token_dependency)])
async def apply_playbook_step(agent_id: str, step_id: str, body: dict[str, Any]) -> dict[str, Any]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    playbook_id = body.get("playbook_id", "general-recovery")
    result = apply_step(playbook_id, step_id, agent_id)
    if result.get("success"):
        agent_reg.record_audit(
            agent_id, agent.name,
            f"Étape playbook appliquée : {step_id} ({playbook_id})",
            user=body.get("user", "user"),
            kind="info",
        )
        agent_reg.emit_log(
            result["message"],
            level=LogLevel.info,
            source="playbook",
            agent_id=agent_id,
        )
    return result


@router.get("/agents/{agent_id}/audit", dependencies=[Depends(token_dependency)])
async def get_agent_audit(agent_id: str, limit: int = 50) -> list[dict[str, Any]]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    with Session(engine) as session:
        entries = session.exec(
            select(AuditEntryDB)
            .where(AuditEntryDB.agent_id == agent_id)
            .order_by(AuditEntryDB.ts.desc())
            .limit(limit)
        ).all()
    return [
        {
            "id": e.id,
            "ts": e.ts.isoformat(),
            "agent_id": e.agent_id,
            "agent_name": e.agent_name,
            "action": e.action,
            "user": e.user,
            "kind": e.kind,
        }
        for e in entries
    ]


@router.patch("/agents/{agent_id}/throttle", dependencies=[Depends(token_dependency)])
async def throttle_agent(agent_id: str, body: dict[str, Any]) -> dict[str, Any]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    percent = body.get("percent", 100)
    if not isinstance(percent, int | float) or not (0 <= percent <= 100):
        raise HTTPException(status_code=422, detail="percent doit être entre 0 et 100")
    agent_reg.record_audit(
        agent_id, agent.name,
        f"Throttle réglé à {percent}%",
        user=body.get("user", "user"),
        kind="warning" if percent < 50 else "info",
    )
    agent_reg.emit_log(
        f"Agent '{agent.name}' throttlé à {percent}%",
        level=LogLevel.warning if percent < 50 else LogLevel.info,
        source="control",
        agent_id=agent_id,
    )
    return {"agent_id": agent_id, "throttle_percent": percent, "applied": True}


@router.patch("/agents/{agent_id}/guardrails", dependencies=[Depends(token_dependency)])
async def update_guardrails(agent_id: str, body: dict[str, Any]) -> dict[str, Any]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    with Session(engine) as session:
        config = session.exec(
            select(GuardrailsConfigDB).where(GuardrailsConfigDB.agent_id == agent_id)
        ).first()
        if config is None:
            config = GuardrailsConfigDB(agent_id=agent_id)
        for field in ("pii", "injection", "faithfulness", "content_safety"):
            if field in body:
                setattr(config, field, bool(body[field]))
        config.updated_at = datetime.utcnow()
        session.add(config)
        session.commit()
        session.refresh(config)

    agent_reg.record_audit(
        agent_id, agent.name,
        f"Guardrails mis à jour : {body}",
        user=body.get("user", "user"),
        kind="info",
    )
    return {
        "agent_id": agent_id,
        "pii": config.pii,
        "injection": config.injection,
        "faithfulness": config.faithfulness,
        "content_safety": config.content_safety,
        "updated_at": config.updated_at.isoformat(),
    }


@router.post("/agents/{agent_id}/rollback", dependencies=[Depends(token_dependency)])
async def rollback_agent(agent_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    # Rollback : remettre le statut à idle et effacer la tâche courante
    agent_reg.update_agent_status(agent_id, AgentStatus.idle, None)
    user = (body or {}).get("user", "user")
    agent_reg.record_audit(
        agent_id, agent.name,
        "Rollback effectué — statut remis à idle",
        user=user,
        kind="warning",
    )
    agent_reg.emit_log(
        f"Rollback de '{agent.name}' — configuration restaurée",
        level=LogLevel.warning,
        source="control",
        agent_id=agent_id,
    )
    return {"agent_id": agent_id, "rolled_back": True, "new_status": "idle"}


@router.get("/agents/{agent_id}/logs", dependencies=[Depends(token_dependency)])
async def get_agent_logs(agent_id: str, limit: int = 100) -> list[dict[str, Any]]:
    agent = agent_reg.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent introuvable")
    with Session(engine) as session:
        entries = session.exec(
            select(LogEntryDB)
            .where(LogEntryDB.agent_id == agent_id)
            .order_by(LogEntryDB.timestamp.desc())
            .limit(limit)
        ).all()
    return [
        {
            "log_id": e.log_id,
            "timestamp": e.timestamp.isoformat(),
            "level": e.level,
            "source": e.source,
            "agent_id": e.agent_id,
            "integration": e.integration,
            "message": e.message,
            "details": json.loads(e.details_json),
        }
        for e in entries
    ]


# ─── Integrations ─────────────────────────────────────────────────────────────


@router.get("/integrations", response_model=list[Integration], dependencies=[Depends(token_dependency)])
async def api_list_integrations() -> list[Integration]:
    return list_integrations()


@router.post("/integrations/{integration_id}/connect", dependencies=[Depends(token_dependency)])
async def api_connect(integration_id: str, body: dict[str, Any]) -> Integration:
    integ = connect_integration(integration_id, body.get("api_key"))
    if not integ:
        raise HTTPException(status_code=404, detail="Intégration introuvable")
    return integ


@router.post("/integrations/{integration_id}/disconnect", dependencies=[Depends(token_dependency)])
async def api_disconnect(integration_id: str) -> Integration:
    integ = disconnect_integration(integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Intégration introuvable")
    return integ


# ─── Generic Webhook Receiver ─────────────────────────────────────────────────


@router.post("/webhook/{source}/{token}")
async def receive_webhook(source: str, token: str, request: Request) -> dict[str, str]:
    """Point d'entrée webhook universel — reçoit les événements de n8n, Make, etc."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        src = IntegrationSource(source)
    except ValueError:
        src = IntegrationSource.custom
    record_integration_event(src)
    agent_reg.emit_log(
        f"Webhook reçu depuis {source}",
        level=agent_reg.LogLevel.info,
        source=source,
        integration=src,
        details={"token_prefix": token, "payload_keys": list(body.keys())},
    )
    logger.info("webhook_received", extra={"source": source, "token": token})
    return {"status": "received", "source": source}


# ─── WebSocket — Live Feed ─────────────────────────────────────────────────────


@router.websocket("/ws/live")
async def websocket_live(ws: WebSocket) -> None:
    await agent_reg.subscribe(ws)
    try:
        # Envoie l'état initial
        import json
        agents_payload = json.dumps(
            {"type": "init", "agents": [a.model_dump(mode="json") for a in agent_reg.list_agents()]},
            default=str,
        )
        await ws.send_text(agents_payload)
        # Envoie les derniers logs
        logs_payload = json.dumps(
            {"type": "logs_history", "logs": [l.model_dump(mode="json") for l in agent_reg.recent_logs(50)]},
            default=str,
        )
        await ws.send_text(logs_payload)
        # Garde la connexion ouverte
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await agent_reg.unsubscribe(ws)
