"""Mission request/response schemas."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Difficulty = Literal["default", "easy", "medium", "hard", "extreme"]
AgentName = Literal["random", "rule_based", "ppo"]
MissionMode = Literal["science", "survival", "exploration", "balanced"]


class CreateMissionRequest(BaseModel):
    difficulty: Difficulty = "medium"
    agent: AgentName = "rule_based"
    mode: MissionMode = "balanced"
    seed: int = Field(default=42, ge=0)
    model_path: str | None = None
    speed: float = Field(default=1.0, gt=0.0, le=20.0)
    max_steps: int | None = Field(default=None, ge=20, le=2000)
    map_size: int | None = Field(default=None, ge=10, le=60)
    multi_agent: bool = False


class MissionSummary(BaseModel):
    id: str
    difficulty: Difficulty
    agent: AgentName
    mode: MissionMode
    seed: int
    status: Literal["running", "paused", "done"]
    step: int
    max_steps: int
    success: bool
    failure_reason: str | None
    multi_agent: bool = False


class MissionDetail(BaseModel):
    id: str
    difficulty: Difficulty
    agent: AgentName
    mode: MissionMode
    seed: int
    status: Literal["running", "paused", "done"]
    state: dict[str, Any]
    decision: dict[str, Any] | None
    events: list[str] = Field(default_factory=list)
    multi_agent: bool = False


class ActionRequest(BaseModel):
    action: int = Field(ge=0, le=10)
