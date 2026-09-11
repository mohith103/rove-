"""Counterfactual analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.api.missions import get_service
from backend.app.schemas.counterfactual import (
    CounterfactualTimeline,
    RunCounterfactualRequest,
    RunCounterfactualResponse,
    TimelineFrame,
)
from backend.app.services.counterfactual_service import run_counterfactual

router = APIRouter(prefix="/counterfactual", tags=["counterfactual"])


@router.post("/{mission_id}", response_model=RunCounterfactualResponse)
def run_cf(
    mission_id: str,
    req: RunCounterfactualRequest,
) -> RunCounterfactualResponse:
    service = get_service()
    mission = service.get(mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="mission not found")
    if mission.status != "done":
        raise HTTPException(
            status_code=400,
            detail="counterfactual requires a completed mission",
        )

    try:
        result = run_counterfactual(
            mission=mission,
            fork_step=req.fork_step,
            override=req.override,
            override_duration=req.override_duration,
            custom_action=req.custom_action,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Convert dict frames into typed models
    def build_timeline(t: dict) -> CounterfactualTimeline:
        return CounterfactualTimeline(
            label=t["label"],
            description=t["description"],
            success=t["success"],
            steps=t["steps"],
            samples_collected=t["samples_collected"],
            energy_left=t["energy_left"],
            oxygen_left=t["oxygen_left"],
            rover_health=t["rover_health"],
            failure_reason=t["failure_reason"],
            frames=[TimelineFrame(**f) for f in t["frames"]],
        )

    return RunCounterfactualResponse(
        mission_id=result["mission_id"],
        fork_step=result["fork_step"],
        override=result["override"],
        override_duration=result["override_duration"],
        actual=build_timeline(result["actual"]),
        counterfactual=build_timeline(result["counterfactual"]),
        verdict=result["verdict"],
    )