"""Simple heuristic planner for ROVE.

The planner enumerates a small set of candidate plans, scores each one
with a weighted objective, and returns the first action of the best plan.

This is intentionally simple — a heuristic/MCTS-style planner comes later
in Phase 10. For Phase 6, the goal is *explainability*, not optimality.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from simulation.environment import Action
from simulation.state import MissionState, ScienceSite


# ---------- Mission modes ----------

@dataclass
class ModeWeights:
    science: float = 1.0
    energy: float = 0.7
    safety: float = 1.0
    exploration: float = 0.6
    time: float = 0.3

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


MODE_PRESETS: dict[str, ModeWeights] = {
    "science":    ModeWeights(science=1.4, energy=0.6, safety=0.8, exploration=1.0, time=0.2),
    "survival":   ModeWeights(science=0.5, energy=1.4, safety=1.6, exploration=0.3, time=0.4),
    "exploration": ModeWeights(science=0.8, energy=0.9, safety=0.9, exploration=1.5, time=0.3),
    "balanced":   ModeWeights(),
}


# ---------- Plan representation ----------

@dataclass
class Plan:
    name: str
    expected_science: float
    expected_energy_cost: float
    expected_risk: float
    steps: int
    action: int  # the first action to take
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------- Planner ----------

class Planner:
    """Evaluates a small set of candidate plans and picks the best."""

    def __init__(self, mode: str = "balanced") -> None:
        if mode not in MODE_PRESETS:
            raise ValueError(f"unknown mission mode: {mode!r}")
        self.mode = mode
        self.weights = MODE_PRESETS[mode]

    def score(self, plan: Plan) -> float:
        w = self.weights
        return (
            w.science * plan.expected_science
            - w.energy * plan.expected_energy_cost
            - w.safety * plan.expected_risk * 100.0
            - w.time * plan.steps
        )

    def candidate_plans(self, state: MissionState) -> list[Plan]:
        """Generate a small set of plausible plans."""
        r = state.rover
        d_base = abs(r.x - state.base.x) + abs(r.y - state.base.y)
        nearest = self._nearest_uncollected(state)

        plans: list[Plan] = []

        # Plan 1: RETURN_TO_BASE (always available)
        plans.append(Plan(
            name="return_to_base",
            expected_science=0.0,
            expected_energy_cost=d_base * 1.2,
            expected_risk=max(0.0, 0.3 - r.energy / 200.0),
            steps=d_base,
            action=Action.RETURN_TO_BASE,
            notes="Head home, recharge, unload cargo.",
        ))

        # Plan 2: VISIT_NEAREST_SITE
        if nearest is not None:
            d_site = abs(nearest.x - r.x) + abs(nearest.y - r.y)
            # Rough estimate: energy cost of going there and back
            energy = (d_site + abs(nearest.x - state.base.x) + abs(nearest.y - state.base.y))
            plans.append(Plan(
                name=f"visit_site_at_{nearest.x}_{nearest.y}",
                expected_science=float(nearest.value),
                expected_energy_cost=float(energy),
                expected_risk=0.3 + 0.1 * nearest.difficulty,
                steps=int(d_site),
                action=self._step_toward(r.x, r.y, nearest.x, nearest.y),
                notes=f"Collect sample worth {nearest.value}.",
            ))

        # Plan 3: REPAIR (if damaged)
        if r.rover_health < 70:
            plans.append(Plan(
                name="repair",
                expected_science=0.0,
                expected_energy_cost=2.0,
                expected_risk=0.0,
                steps=1,
                action=Action.REPAIR,
                notes="Fix rover before continuing.",
            ))

        # Plan 4: RECHARGE (only meaningful at base)
        if (r.x, r.y) == (state.base.x, state.base.y):
            plans.append(Plan(
                name="recharge",
                expected_science=0.0,
                expected_energy_cost=-10.0,   # negative = gains energy
                expected_risk=0.0,
                steps=1,
                action=Action.RECHARGE,
                notes="Top up energy at base.",
            ))

        return plans

    def choose(self, state: MissionState) -> tuple[Plan, list[tuple[Plan, float]]]:
        """Return the best plan and a scored list of all candidates."""
        plans = self.candidate_plans(state)
        scored = [(p, self.score(p)) for p in plans]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[0][0], scored

    # ---------- Helpers ----------

    def _nearest_uncollected(self, state: MissionState) -> ScienceSite | None:
        remaining = [s for s in state.science_sites if not s.collected]
        if not remaining:
            return None
        r = state.rover
        return min(remaining, key=lambda s: abs(s.x - r.x) + abs(s.y - r.y))

    def _step_toward(self, x: int, y: int, tx: int, ty: int) -> int:
        dx = tx - x
        dy = ty - y
        if abs(dx) >= abs(dy):
            if dx > 0:
                return Action.MOVE_EAST
            if dx < 0:
                return Action.MOVE_WEST
        if dy > 0:
            return Action.MOVE_SOUTH
        if dy < 0:
            return Action.MOVE_NORTH
        return Action.WAIT