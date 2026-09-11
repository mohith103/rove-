"""Resource specialist: optimizes energy and life support efficiency."""
from __future__ import annotations

from agents.pathfinding import next_step_toward
from agents.specialists.base import Specialist, SpecialistProposal
from simulation.environment import Action
from simulation.state import MissionState
from simulation.terrain import TerrainType


class ResourceSpecialist(Specialist):
    name = "resource"

    def propose(self, state: MissionState) -> SpecialistProposal:
        rover = state.rover
        base = state.base
        terrain = state.terrain
        at_base = (rover.x, rover.y) == (base.x, base.y)

        if at_base and rover.energy < 80.0:
            return SpecialistProposal(
                specialist=self.name,
                action=Action.RECHARGE,
                weight=0.8,
                rationale=f"At base, energy {rover.energy:.1f}% — top up.",
            )

        if rover.energy < 40.0 and not at_base:
            return SpecialistProposal(
                specialist=self.name,
                action=Action.RETURN_TO_BASE,
                weight=0.7,
                rationale=f"Energy {rover.energy:.1f}% — reserve buffer.",
            )

        current = terrain.get(rover.x, rover.y)
        if current in (TerrainType.ROCK, TerrainType.CRATER) and not at_base:
            for dx, dy, action in [
                (0, -1, Action.MOVE_NORTH),
                (0, 1, Action.MOVE_SOUTH),
                (1, 0, Action.MOVE_EAST),
                (-1, 0, Action.MOVE_WEST),
            ]:
                nx, ny = rover.x + dx, rover.y + dy
                if not terrain.is_passable(nx, ny):
                    continue
                neighbor = terrain.get(nx, ny)
                if neighbor not in (TerrainType.ROCK, TerrainType.CRATER):
                    return SpecialistProposal(
                        specialist=self.name,
                        action=action,
                        weight=0.65,
                        rationale="Moving off expensive terrain.",
                    )

        target = self._nearest_uncollected(state)
        if target is not None:
            action = next_step_toward(terrain, (rover.x, rover.y), (target.x, target.y))
            return SpecialistProposal(
                specialist=self.name,
                action=action,
                weight=0.6,
                rationale="Efficient path toward nearest science site.",
            )

        return SpecialistProposal(
            specialist=self.name,
            action=Action.WAIT,
            weight=0.2,
            rationale="No resource decision to make.",
        )

    def _nearest_uncollected(self, state: MissionState):
        remaining = [s for s in state.science_sites if not s.collected]
        if not remaining:
            return None
        r = state.rover
        return min(remaining, key=lambda s: abs(s.x - r.x) + abs(s.y - r.y))
