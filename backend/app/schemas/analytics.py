"""Analytics schemas for mission summaries."""
from __future__ import annotations

from pydantic import BaseModel, Field


class MissionAnalytics(BaseModel):
    mission_id: str
    steps_taken: int
    samples_collected: int
    energy_left: float
    oxygen_left: float
    success: bool
    failure_reason: str | None
    events_encountered: int
    decisions_taken: int = Field(default=0)