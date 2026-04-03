import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect

from app.agents import registry as agent_reg
from app.core.auth import token_dependency
from app.integrations.manager import (
    connect_integration,
    disconnect_integration,
    get_integration,
    list_integrations,
    record_integration_event,
)
from app.models.schemas import (
    AIEvent,
    Anomaly,
    Agent,
    AgentStatus,
    Integration,
    IntegrationSource,
    LogEntry,
    MetricsSnapshot,
)
from app.services.pipeline import ProcessingPipeline

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
