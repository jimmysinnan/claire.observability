import json
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.utcnow()


# ─── Agent ───────────────────────────────────────────────────────────────────


class AgentDB(SQLModel, table=True):
    __tablename__ = "agent"

    agent_id: str = Field(primary_key=True)
    name: str
    integration: str
    status: str = "idle"
    current_task: Optional[str] = None
    runs_today: int = 0
    errors_today: int = 0
    success_rate: float = 100.0
    last_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_now)
    tags_json: str = Field(default="[]")
    webhook_secret: Optional[str] = None
    latency_ms: Optional[float] = None
    events_total: int = 0
    anomalies_count: int = 0
    health_score: float = 100.0


# ─── AgentRun ─────────────────────────────────────────────────────────────────


class AgentRunDB(SQLModel, table=True):
    __tablename__ = "agent_run"

    run_id: str = Field(primary_key=True)
    agent_id: str = Field(index=True)
    status: str = "running"
    started_at: datetime = Field(default_factory=_now)
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    trigger: str = "manual"
    output_json: str = Field(default="{}")
    error: Optional[str] = None


# ─── LogEntry ────────────────────────────────────────────────────────────────


class LogEntryDB(SQLModel, table=True):
    __tablename__ = "log_entry"

    log_id: str = Field(primary_key=True)
    timestamp: datetime = Field(default_factory=_now, index=True)
    level: str = "INFO"
    source: str = "system"
    agent_id: Optional[str] = Field(default=None, index=True)
    integration: Optional[str] = None
    message: str
    details_json: str = Field(default="{}")


# ─── Anomaly ────────────────────────────────────────────────────────────────


class AnomalyDB(SQLModel, table=True):
    __tablename__ = "anomaly"

    anomaly_id: str = Field(primary_key=True)
    event_id: str
    agent_id: Optional[str] = Field(default=None, index=True)
    rule_name: str
    severity: str = "low"
    reason: str
    created_at: datetime = Field(default_factory=_now, index=True)
    extra_json: str = Field(default="{}")


# ─── AuditEntry ──────────────────────────────────────────────────────────────


class AuditEntryDB(SQLModel, table=True):
    __tablename__ = "audit_entry"

    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=_now, index=True)
    agent_id: str = Field(index=True)
    agent_name: str
    action: str
    user: str = "system"
    kind: str = "info"


# ─── GuardrailsConfig ────────────────────────────────────────────────────────


class GuardrailsConfigDB(SQLModel, table=True):
    __tablename__ = "guardrails_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(index=True, unique=True)
    pii: bool = True
    injection: bool = True
    faithfulness: bool = False
    content_safety: bool = True
    updated_at: datetime = Field(default_factory=_now)


# ─── GovernanceMetric ────────────────────────────────────────────────────────


class GovernanceMetricDB(SQLModel, table=True):
    __tablename__ = "governance_metric"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(index=True)
    adherence: float = 0.0
    tool_accuracy: float = 0.0
    context_relevance: float = 0.0
    answer_correctness: float = 0.0
    pii_blocked: int = 0
    injection_blocked: int = 0
    recorded_at: datetime = Field(default_factory=_now, index=True)
