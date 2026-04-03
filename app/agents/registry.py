"""
AgentRegistry — source de vérité pour tous les agents observés.
Gère le cycle de vie, les runs, et le broadcast WebSocket en temps réel.
"""
import asyncio
import json
import logging
import uuid
from collections import deque
from datetime import datetime
from typing import Any

from fastapi import WebSocket

from app.models.schemas import (
    Agent,
    AgentRun,
    AgentStatus,
    IntegrationSource,
    LogEntry,
    LogLevel,
)

logger = logging.getLogger(__name__)

# ─── Live Log Bus ─────────────────────────────────────────────────────────────

_log_bus: deque[LogEntry] = deque(maxlen=1000)
_ws_clients: list[WebSocket] = []


async def broadcast(message: dict[str, Any]) -> None:
    """Diffuse un message JSON à tous les clients WebSocket connectés."""
    dead: list[WebSocket] = []
    payload = json.dumps(message, default=str)
    for ws in _ws_clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.remove(ws)


async def subscribe(ws: WebSocket) -> None:
    await ws.accept()
    _ws_clients.append(ws)


async def unsubscribe(ws: WebSocket) -> None:
    if ws in _ws_clients:
        _ws_clients.remove(ws)


def emit_log(
    message: str,
    level: LogLevel = LogLevel.info,
    source: str = "system",
    agent_id: str | None = None,
    integration: IntegrationSource | None = None,
    details: dict[str, Any] | None = None,
) -> LogEntry:
    entry = LogEntry(
        log_id=str(uuid.uuid4()),
        level=level,
        source=source,
        agent_id=agent_id,
        integration=integration,
        message=message,
        details=details or {},
    )
    _log_bus.append(entry)
    asyncio.create_task(
        broadcast({"type": "log", "data": entry.model_dump(mode="json")})
    )
    return entry


def recent_logs(limit: int = 200) -> list[LogEntry]:
    return list(_log_bus)[-limit:]


# ─── Agent Registry ───────────────────────────────────────────────────────────

_agents: dict[str, Agent] = {}
_runs: dict[str, list[AgentRun]] = {}


def _broadcast_agent(agent: Agent) -> None:
    asyncio.create_task(
        broadcast({"type": "agent_update", "data": agent.model_dump(mode="json")})
    )


def register_agent(
    name: str,
    integration: IntegrationSource,
    tags: list[str] | None = None,
) -> Agent:
    agent_id = str(uuid.uuid4())
    agent = Agent(
        agent_id=agent_id,
        name=name,
        integration=integration,
        tags=tags or [],
    )
    _agents[agent_id] = agent
    _runs[agent_id] = []
    emit_log(
        f"Agent '{name}' enregistré ({integration.value})",
        level=LogLevel.info,
        source="registry",
        agent_id=agent_id,
        integration=integration,
    )
    _broadcast_agent(agent)
    return agent


def get_agent(agent_id: str) -> Agent | None:
    return _agents.get(agent_id)


def list_agents() -> list[Agent]:
    return list(_agents.values())


def update_agent_status(
    agent_id: str,
    status: AgentStatus,
    current_task: str | None = None,
) -> Agent | None:
    agent = _agents.get(agent_id)
    if not agent:
        return None
    agent.status = status
    agent.current_task = current_task
    if status == AgentStatus.running:
        agent.runs_today += 1
        agent.last_run_at = datetime.utcnow()
    elif status == AgentStatus.error:
        agent.errors_today += 1
    total = agent.runs_today
    errors = agent.errors_today
    agent.success_rate = round((total - errors) / total * 100, 1) if total else 100.0
    _broadcast_agent(agent)
    return agent


def record_run(
    agent_id: str,
    status: str,
    trigger: str = "webhook",
    duration_ms: int | None = None,
    output: dict[str, Any] | None = None,
    error: str | None = None,
) -> AgentRun | None:
    agent = _agents.get(agent_id)
    if not agent:
        return None
    run = AgentRun(
        run_id=str(uuid.uuid4()),
        agent_id=agent_id,
        status=status,
        finished_at=datetime.utcnow() if status != "running" else None,
        duration_ms=duration_ms,
        trigger=trigger,
        output=output or {},
        error=error,
    )
    _runs.setdefault(agent_id, []).append(run)
    level = LogLevel.success if status == "success" else (
        LogLevel.error if status == "error" else LogLevel.info
    )
    emit_log(
        f"Run {status} pour '{agent.name}' ({duration_ms}ms)" if duration_ms else f"Run {status} pour '{agent.name}'",
        level=level,
        source=agent.integration.value,
        agent_id=agent_id,
        integration=agent.integration,
        details={"run_id": run.run_id, "trigger": trigger},
    )
    return run


def get_runs(agent_id: str, limit: int = 20) -> list[AgentRun]:
    return list(_runs.get(agent_id, []))[-limit:]


def delete_agent(agent_id: str) -> bool:
    if agent_id not in _agents:
        return False
    name = _agents[agent_id].name
    del _agents[agent_id]
    _runs.pop(agent_id, None)
    emit_log(
        f"Agent '{name}' supprimé",
        level=LogLevel.warning,
        source="registry",
    )
    asyncio.create_task(broadcast({"type": "agent_deleted", "data": {"agent_id": agent_id}}))
    return True


def _seed_demo_agents() -> None:
    """Peuple quelques agents de démonstration au démarrage."""
    demos = [
        ("n8n Automation", IntegrationSource.n8n, ["automation", "demo"], AgentStatus.running, "Traitement webhook Stripe"),
        ("Claude Assistant", IntegrationSource.claude, ["ai", "support"], AgentStatus.idle, None),
        ("Make Scenario", IntegrationSource.make, ["automation"], AgentStatus.running, "Sync CRM → Notion"),
        ("ChatGPT Agent", IntegrationSource.openai, ["ai"], AgentStatus.error, None),
        ("Gemini Pipeline", IntegrationSource.gemini, ["ai", "data"], AgentStatus.paused, None),
    ]
    for name, integration, tags, status, task in demos:
        agent = register_agent(name, integration, tags)
        import random
        agent.runs_today = random.randint(5, 120)
        agent.errors_today = random.randint(0, 5)
        total = agent.runs_today
        errors = agent.errors_today
        agent.success_rate = round((total - errors) / total * 100, 1) if total else 100.0
        agent.last_run_at = datetime.utcnow()
        agent.status = status
        agent.current_task = task
