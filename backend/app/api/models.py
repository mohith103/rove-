"""Model/agent discovery endpoints."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/models", tags=["models"])


AVAILABLE_AGENTS = [
    {"name": "random", "description": "Uniform random baseline."},
    {"name": "rule_based", "description": "Hand-crafted IF-THEN commander."},
    {"name": "ppo", "description": "PPO agent trained with Stable-Baselines3."},
]


@router.get("")
def list_models() -> dict:
    return {"agents": AVAILABLE_AGENTS}