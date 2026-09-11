"""REST endpoints for missions."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.schemas.mission import (
    ActionRequest,
    CreateMissionRequest,
    MissionDetail,
    MissionSummary,
)
from backend.app.services.mission_service import MissionService
from backend.app.services.runner import MissionRunner
from simulation.environment import Action

router = APIRouter(prefix="/missions", tags=["missions"])

_service = MissionService()
_runners: dict[str, MissionRunner] = {}


def get_service() -> MissionService:
    return _service


@router.post("", response_model=MissionSummary)
def create_mission(req: CreateMissionRequest) -> MissionSummary:
    mission = _service.create_mission(
        difficulty=req.difficulty,
        agent_name=req.agent,
        mode=req.mode,
        seed=req.seed,
        model_path=req.model_path,
        max_steps=req.max_steps,
        multi_agent=req.multi_agent,
    )
    runner = MissionRunner(mission, speed=req.speed)
    runner.start()
    _runners[mission.id] = runner
    return MissionSummary(**mission.to_summary())


@router.get("", response_model=list[MissionSummary])
def list_missions() -> list[MissionSummary]:
    return [MissionSummary(**m.to_summary()) for m in _service.list_all()]


@router.get("/{mission_id}", response_model=MissionDetail)
def get_mission(mission_id: str) -> MissionDetail:
    m = _service.get(mission_id)
    if m is None:
        raise HTTPException(status_code=404, detail="mission not found")
    return MissionDetail(**m.to_detail())


@router.post("/{mission_id}/pause", response_model=MissionSummary)
def pause_mission(mission_id: str) -> MissionSummary:
    m = _service.get(mission_id)
    if m is None:
        raise HTTPException(status_code=404, detail="mission not found")
    _service.pause(mission_id)
    return MissionSummary(**m.to_summary())


@router.post("/{mission_id}/resume", response_model=MissionSummary)
def resume_mission(mission_id: str) -> MissionSummary:
    m = _service.get(mission_id)
    if m is None:
        raise HTTPException(status_code=404, detail="mission not found")
    _service.resume(mission_id)
    return MissionSummary(**m.to_summary())


@router.post("/{mission_id}/action", response_model=MissionSummary)
def apply_action(mission_id: str, req: ActionRequest) -> MissionSummary:
    m = _service.get(mission_id)
    if m is None:
        raise HTTPException(status_code=404, detail="mission not found")
    if not _service.step_manual(mission_id, req.action):
        raise HTTPException(status_code=400, detail="could not apply action")
    return MissionSummary(**m.to_summary())


@router.get("/{mission_id}/actions", response_model=dict[str, str])
def list_actions(mission_id: str) -> dict[str, str]:
    return {str(k): v for k, v in Action.NAMES.items()}


@router.get("/{mission_id}/replay")
def get_replay(mission_id: str) -> dict:
    m = _service.get(mission_id)
    if m is None:
        raise HTTPException(status_code=404, detail="mission not found")
    return m.to_replay()
