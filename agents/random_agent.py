"""Random agent — baseline for comparison."""
from __future__ import annotations

import numpy as np

from agents.base_agent import BaseAgent
from simulation.environment import Action
from simulation.state import MissionState


class RandomAgent(BaseAgent):
    """Picks a uniformly random action every step."""

    name = "random"

    def __init__(self, seed: int = 0) -> None:
        self.rng = np.random.default_rng(seed)

    def act(self, state: MissionState) -> int:
        return int(self.rng.integers(0, Action.N_ACTIONS))