"""Failure analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.api.missions import get_service
from backend.app.schemas.analysis import AnalysisResponse, CriticalMoment
from backend.app.services.failure_analysis_service import analyze_mission

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{mission_id}", response_model=AnalysisResponse)
def get_analysis(mission_id: str) -> AnalysisResponse:
    service = get_service()
    mission = service.get(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="mission not found")
    if mission.status != "done":
        raise HTTPException(
            status_code=400,
            detail="analysis requires a completed mission",
        )

    result = analyze_mission(mission)

    return AnalysisResponse(
        mission_id=result["mission_id"],
        success=result["success"],
        primary_cause=result["primary_cause"],
        contributing_factors=result["contributing_factors"],
        recommendations=result["recommendations"],
        critical_moments=[CriticalMoment(**m) for m in result["critical_moments"]],
        summary=result["summary"],
    )
