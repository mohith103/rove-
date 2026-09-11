"""Batch experiment endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.schemas.experiment import (
    RunExperimentRequest,
    RunExperimentResponse,
    ExperimentRow,
)
from backend.app.services.experiment_service import run_batch

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=RunExperimentResponse)
def create_experiment(req: RunExperimentRequest) -> RunExperimentResponse:
    """Run a batch of missions and return aggregated results."""
    if len(req.agents) * len(req.difficulties) * req.episodes > 500:
        raise HTTPException(
            status_code=400,
            detail="Too many missions. Max is 500 per request.",
        )

    try:
        rows, total, elapsed = run_batch(
            agents=req.agents,
            difficulties=req.difficulties,
            mode=req.mode,
            episodes=req.episodes,
            seed=req.seed,
            max_steps=req.max_steps,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return RunExperimentResponse(
        rows=[ExperimentRow(**r) for r in rows],
        total_missions=total,
        elapsed_seconds=elapsed,
    )
