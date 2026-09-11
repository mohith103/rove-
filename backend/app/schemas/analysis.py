"""Schemas for mission failure analysis."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CriticalMoment(BaseModel):
    step: int
    label: str
    detail: str
    severity: str  # "info" | "warning" | "critical"


class AnalysisResponse(BaseModel):
    mission_id: str
    success: bool
    primary_cause: str
    contributing_factors: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    critical_moments: list[CriticalMoment] = Field(default_factory=list)
    summary: str
