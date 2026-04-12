"""
AgentRegistry — source de vérité pour tous les agents observés.
Gère le cycle de vie, les runs, et le broadcast WebSocket en temps réel.
Agents et runs sont persistés en SQLite. Le bus de logs live reste en mémoire.
"""
import asyncio
import json
import logging
import uuid
from collections import deque
from datetime import datetime
from typing import Any

from fastapi import WebSocket
from sqlmodel import Session, select

from app.core.database import engine
from app.models.db_models import AgentDB, AgentRunDB, AuditEntryDB, LogEntryDB
from app.models.schemas import (
    Agent,
    AgentRun,
    AgentStatus,
    IntegrationSource,
    LogEntry,
    LogLevel,
)

logger = logging.getLogger(__name__)

# ─── Live Log Bus (in-memory, temps réel uniquement) ─────────────────────────

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
    # Persist to SQLite
    with Session(engine) as session:
        db_entry = LogEntryDB(
            log_id=entry.log_id,
            timestamp=entry.timestamp,
            level=entry.level.value,
            source=entry.source,
            agent_id=entry.agent_id,
            integration=entry.integration.value if entry.integration else None,
            message=entry.message,
            details_json=json.dumps(entry.details),
        )
        session.add(db_entry)
        session.commit()
    asyncio.create_task(
        broadcast({"type": "log", "data": entry.model_dump(mode="json")})
    )
    return entry


def recent_logs(limit: int = 200) -> list[LogEntry]:
    return list(_log_bus)[-limit:]


# ─── Helpers DB → Schema ──────────────────────────────────────────────────────


def _agent_from_db(db: AgentDB) -> Agent:
    return Agent(
        agent_id=db.agent_id,
        name=db.name,
        integration=IntegrationSource(db.integration),
        status=AgentStatus(db.status),
        current_task=db.current_task,
        runs_today=db.runs_today,
        errors_today=db.errors_today,
        success_rate=db.success_rate,
        last_run_at=db.last_run_at,
        created_at=db.created_at,
        tags=json.loads(db.tags_json),
        webhook_secret=db.webhook_secret,
        # Extra fields passed via model_config extra="allow"
        latency_ms=db.latency_ms,
        events_total=db.events_total,
        anomalies_count=db.anomalies_count,
        health_score=db.health_score,
    )


def _run_from_db(db: AgentRunDB) -> AgentRun:
    return AgentRun(
        run_id=db.run_id,
        agent_id=db.agent_id,
        status=db.status,
        started_at=db.started_at,
        finished_at=db.finished_at,
        duration_ms=db.duration_ms,
        trigger=db.trigger,
        output=json.loads(db.output_json),
        error=db.error,
    )


# ─── Agent Registry ───────────────────────────────────────────────────────────


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
    db_agent = AgentDB(
        agent_id=agent_id,
        name=name,
        integration=integration.value,
        tags_json=json.dumps(tags or []),
    )
    with Session(engine) as session:
        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)

    agent = _agent_from_db(db_agent)
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
    with Session(engine) as session:
        db_agent = session.get(AgentDB, agent_id)
        if db_agent is None:
            return None
        return _agent_from_db(db_agent)


def list_agents() -> list[Agent]:
    with Session(engine) as session:
        agents = session.exec(select(AgentDB)).all()
        return [_agent_from_db(a) for a in agents]


def update_agent_status(
    agent_id: str,
    status: AgentStatus,
    current_task: str | None = None,
) -> Agent | None:
    with Session(engine) as session:
        db_agent = session.get(AgentDB, agent_id)
        if db_agent is None:
            return None
        db_agent.status = status.value
        db_agent.current_task = current_task
        if status == AgentStatus.running:
            db_agent.runs_today += 1
            db_agent.last_run_at = datetime.utcnow()
        elif status == AgentStatus.error:
            db_agent.errors_today += 1
        total = db_agent.runs_today
        errors = db_agent.errors_today
        db_agent.success_rate = round((total - errors) / total * 100, 1) if total else 100.0
        session.add(db_agent)
        session.commit()
        session.refresh(db_agent)
        agent = _agent_from_db(db_agent)

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
    agent = get_agent(agent_id)
    if not agent:
        return None
    run_id = str(uuid.uuid4())
    db_run = AgentRunDB(
        run_id=run_id,
        agent_id=agent_id,
        status=status,
        finished_at=datetime.utcnow() if status != "running" else None,
        duration_ms=duration_ms,
        trigger=trigger,
        output_json=json.dumps(output or {}),
        error=error,
    )
    with Session(engine) as session:
        session.add(db_run)
        session.commit()
        session.refresh(db_run)
        run = _run_from_db(db_run)

    level = LogLevel.success if status == "success" else (
        LogLevel.error if status == "error" else LogLevel.info
    )
    emit_log(
        f"Run {status} pour '{agent.name}' ({duration_ms}ms)" if duration_ms else f"Run {status} pour '{agent.name}'",
        level=level,
        source=agent.integration.value,
        agent_id=agent_id,
        integration=agent.integration,
        details={"run_id": run_id, "trigger": trigger},
    )
    return run


def get_runs(agent_id: str, limit: int = 20) -> list[AgentRun]:
    with Session(engine) as session:
        runs = session.exec(
            select(AgentRunDB)
            .where(AgentRunDB.agent_id == agent_id)
            .order_by(AgentRunDB.started_at.desc())
            .limit(limit)
        ).all()
        return [_run_from_db(r) for r in runs]


def delete_agent(agent_id: str) -> bool:
    with Session(engine) as session:
        db_agent = session.get(AgentDB, agent_id)
        if db_agent is None:
            return False
        name = db_agent.name
        session.delete(db_agent)
        session.commit()

    emit_log(
        f"Agent '{name}' supprimé",
        level=LogLevel.warning,
        source="registry",
    )
    asyncio.create_task(broadcast({"type": "agent_deleted", "data": {"agent_id": agent_id}}))
    return True


def record_audit(
    agent_id: str,
    agent_name: str,
    action: str,
    user: str = "system",
    kind: str = "info",
) -> AuditEntryDB:
    db_entry = AuditEntryDB(
        agent_id=agent_id,
        agent_name=agent_name,
        action=action,
        user=user,
        kind=kind,
    )
    with Session(engine) as session:
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
    return db_entry


def _seed_demo_agents() -> None:
    """Peuple quelques agents de démonstration au démarrage (idempotent)."""
    # Ne pas reseed si des agents existent déjà
    with Session(engine) as session:
        existing = session.exec(select(AgentDB)).first()
        if existing:
            return

    import random

    demos = [
        ("n8n Automation", IntegrationSource.n8n, ["automation", "demo"], AgentStatus.running, "Traitement webhook Stripe"),
        ("Claude Assistant", IntegrationSource.claude, ["ai", "support"], AgentStatus.idle, None),
        ("Make Scenario", IntegrationSource.make, ["automation"], AgentStatus.running, "Sync CRM → Notion"),
        ("ChatGPT Agent", IntegrationSource.openai, ["ai"], AgentStatus.error, None),
        ("Gemini Pipeline", IntegrationSource.gemini, ["ai", "data"], AgentStatus.paused, None),
    ]
    for name, integration, tags, status, task in demos:
        agent = register_agent(name, integration, tags)
        with Session(engine) as session:
            db_agent = session.get(AgentDB, agent.agent_id)
            if db_agent is None:
                continue
            db_agent.runs_today = random.randint(5, 120)
            db_agent.errors_today = random.randint(0, 5)
            total = db_agent.runs_today
            errors = db_agent.errors_today
            db_agent.success_rate = round((total - errors) / total * 100, 1) if total else 100.0
            db_agent.last_run_at = datetime.utcnow()
            db_agent.status = status.value
            db_agent.current_task = task
            db_agent.latency_ms = round(random.uniform(80, 2400), 1)
            db_agent.events_total = random.randint(10, 500)
            db_agent.anomalies_count = random.randint(0, 8)
            db_agent.health_score = round(random.uniform(55, 100), 1)
            session.add(db_agent)
            session.commit()
