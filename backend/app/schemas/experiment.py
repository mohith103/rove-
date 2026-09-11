"""Schemas for batch experiments."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AgentName = Literal["random", "rule_based", "ppo"]
Difficulty = Literal["default", "easy", "medium", "hard", "extreme"]
Mode = Literal["science", "survival", "exploration", "balanced"]


class RunExperimentRequest(BaseModel):
    agents: list[AgentName] = Field(default_factory=lambda: ["random", "rule_based"])
    difficulties: list[Difficulty] = Field(default_factory=lambda: ["medium"])
    mode: Mode = "balanced"
    episodes: int = Field(default=10, ge=1, le=100)
    seed: int = Field(default=42, ge=0)
    max_steps: int | None = Field(default=None, ge=20, le=2000)


class ExperimentRow(BaseModel):
    agent: str
    difficulty: str
    episodes: int
    success_rate: float
    avg_samples: float
    avg_steps: float
    avg_energy_left: float
    avg_oxygen_left: float
    avg_reward: float
    top_failure: str


class RunExperimentResponse(BaseModel):
    rows: list[ExperimentRow]
    total_missions: int
    elapsed_seconds: float
