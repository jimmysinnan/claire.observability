from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    prediction = "prediction"
    recommendation = "recommendation"
    support_response = "support_response"


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


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


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
