"""Navigation specialist: moves toward the next science target."""
from __future__ import annotations

from agents.pathfinding import next_step_toward
from agents.specialists.base import Specialist, SpecialistProposal
from simulation.environment import Action
from simulation.state import MissionState, ScienceSite


class NavigationSpecialist(Specialist):
    name = "navigation"

    def propose(self, state: MissionState) -> SpecialistProposal:
        rover = state.rover
        base = state.base
        terrain = state.terrain

        required = 3
        if rover.samples_collected >= required:
            if (rover.x, rover.y) != (base.x, base.y):
                action = next_step_toward(terrain, (rover.x, rover.y), (base.x, base.y))
                return SpecialistProposal(
                    specialist=self.name,
                    action=action,
                    weight=0.9,
                    rationale="Enough samples; navigating home.",
                )
            return SpecialistProposal(
                specialist=self.name,
                action=Action.WAIT,
                weight=0.3,
                rationale="At base with enough samples.",
            )

        target = self._nearest_uncollected(state)
        if target is None:
            if (rover.x, rover.y) != (base.x, base.y):
                action = next_step_toward(terrain, (rover.x, rover.y), (base.x, base.y))
                return SpecialistProposal(
                    specialist=self.name,
                    action=action,
                    weight=0.8,
                    rationale="No science targets remain; heading home.",
                )
            return SpecialistProposal(
                specialist=self.name,
                action=Action.WAIT,
                weight=0.2,
                rationale="No targets and at base.",
            )

        action = next_step_toward(terrain, (rover.x, rover.y), (target.x, target.y))
        dist = abs(target.x - rover.x) + abs(target.y - rover.y)
        return SpecialistProposal(
            specialist=self.name,
            action=action,
            weight=0.7,
            rationale=f"Navigating toward site at ({target.x},{target.y}), {dist} cells away.",
        )

    def _nearest_uncollected(self, state: MissionState) -> ScienceSite | None:
        remaining = [s for s in state.science_sites if not s.collected]
        if not remaining:
            return None
        r = state.rover
        return min(remaining, key=lambda s: abs(s.x - r.x) + abs(s.y - r.y))
