from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ─── AI Events ──────────────────────────────────────────────────────────────


class EventType(str, Enum):
    prediction = "prediction"
    recommendation = "recommendation"
    support_response = "support_response"
    automation = "automation"
    api_call = "api_call"


class EventMetadata(BaseModel):
    user_id_hash: str | None = Field(default=None, description="Hashed user id only")
    session_id: str | None = None
    agent_version: str
    source: str = "agent"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIEvent(BaseModel):
    event_id: str
    event_type: EventType
    prompt: str
    context: dict[str, Any] = Field(default_factory=dict)
    prediction: dict[str, Any] = Field(default_factory=dict)
    metadata: EventMetadata

    model_config = ConfigDict(extra="allow")


class NormalizedEvent(BaseModel):
    event_id: str
    event_type: EventType
    timestamp: datetime
    product_ids: list[str] = Field(default_factory=list)
    price_candidates: list[float] = Field(default_factory=list)
    stock_state: dict[str, int] = Field(default_factory=dict)
    prompt_tokens: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


# ─── Anomalies ───────────────────────────────────────────────────────────────


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Anomaly(BaseModel):
    anomaly_id: str
    event_id: str
    rule_name: str
    severity: Severity
    reason: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricsSnapshot(BaseModel):
    total_events: int
    anomalies_detected: int
    anomalies_by_rule: dict[str, int]


# ─── Agents ──────────────────────────────────────────────────────────────────


class AgentStatus(str, Enum):
    running = "running"
    idle = "idle"
    error = "error"
    paused = "paused"
    offline = "offline"


class IntegrationSource(str, Enum):
    n8n = "n8n"
    make = "make"
    claude = "claude"
    openai = "openai"
    gemini = "gemini"
    custom = "custom"


class Agent(BaseModel):
    agent_id: str
    name: str
    integration: IntegrationSource
    status: AgentStatus = AgentStatus.idle
    current_task: str | None = None
    runs_today: int = 0
    errors_today: int = 0
    success_rate: float = 100.0
    last_run_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)
    webhook_secret: str | None = None

    model_config = ConfigDict(extra="allow")


class AgentRun(BaseModel):
    run_id: str
    agent_id: str
    status: str  # "success" | "error" | "running"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    duration_ms: int | None = None
    trigger: str = "manual"
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


# ─── Integrations ────────────────────────────────────────────────────────────


class IntegrationStatus(str, Enum):
    connected = "connected"
    disconnected = "disconnected"
    error = "error"
    pending = "pending"


class Integration(BaseModel):
    integration_id: str
    name: str
    source: IntegrationSource
    status: IntegrationStatus = IntegrationStatus.disconnected
    webhook_url: str | None = None
    api_key_set: bool = False
    last_event_at: datetime | None = None
    events_total: int = 0
    description: str = ""

    model_config = ConfigDict(extra="allow")


# ─── Live Logs ───────────────────────────────────────────────────────────────


class LogLevel(str, Enum):
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    debug = "DEBUG"
    success = "SUCCESS"


class LogEntry(BaseModel):
    log_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel = LogLevel.info
    source: str = "system"
    agent_id: str | None = None
    integration: IntegrationSource | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
