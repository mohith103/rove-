"""Schemas for counterfactual simulations."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


OverrideType = Literal[
    "force_return_to_base",
    "force_recharge",
    "force_repair",
    "force_wait",
    "custom_action",
]


class RunCounterfactualRequest(BaseModel):
    """Request a counterfactual fork from a specific step."""
    fork_step: int = Field(
        ...,
        ge=1,
        description="SOL at which to branch from the original timeline.",
    )
    override: OverrideType = Field(
        default="force_return_to_base",
        description="Policy to apply after the fork point.",
    )
    override_duration: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Number of steps to apply the override policy for. "
        "After this, the original policy resumes.",
    )
    custom_action: int | None = Field(
        default=None,
        ge=0,
        le=10,
        description="Action ID when override == 'custom_action'.",
    )


class TimelineFrame(BaseModel):
    step: int
    rover: dict[str, Any]
    base: dict[str, Any]
    science_sites: list[dict[str, Any]]
    done: bool
    success: bool
    failure_reason: str | None


class CounterfactualTimeline(BaseModel):
    label: str                    # "actual" or "counterfactual"
    description: str              # human-readable summary
    success: bool
    steps: int
    samples_collected: int
    energy_left: float
    oxygen_left: float
    rover_health: float
    failure_reason: str | None
    frames: list[TimelineFrame]


class RunCounterfactualResponse(BaseModel):
    mission_id: str
    fork_step: int
    override: str
    override_duration: int
    actual: CounterfactualTimeline
    counterfactual: CounterfactualTimeline
    verdict: str                  # short textual verdict, e.g. "Counterfactual succeeded where actual failed"