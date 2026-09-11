"""Rule-based commander for ROVE.

Implements a priority list of IF-THEN rules. Movement uses BFS pathfinding
so the rover navigates around mountains and other obstacles.
"""
from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.pathfinding import next_step_toward
from simulation.environment import Action
from simulation.state import MissionState, ScienceSite


class RuleBasedAgent(BaseAgent):
    """A hand-crafted agent with a fixed priority list.

    Priority:
        1. Critical oxygen -> return to base
        2. Critical energy -> return to base (or recharge if at base)
        3. Damaged rover   -> repair
        4. At base + low energy -> recharge
        5. Standing on uncollected site -> collect
        6. Cargo full      -> return to base
        7. Enough samples + near base -> go home
        8. Default         -> move to nearest uncollected site
    """

    name = "rule_based"

    # Tunable thresholds
    OXYGEN_CRITICAL = 25.0
    ENERGY_CRITICAL = 20.0
    ENERGY_LOW = 80.0
    HEALTH_DAMAGED = 40.0

    def act(self, state: MissionState) -> int:
        rover = state.rover
        base = state.base
        terrain = state.terrain

        at_base = (rover.x, rover.y) == (base.x, base.y)

        # 1. Oxygen critical -> return home
        if rover.oxygen < self.OXYGEN_CRITICAL and not at_base:
            return next_step_toward(terrain, (rover.x, rover.y), (base.x, base.y))

        # 2. Energy critical -> return home (or recharge if already there)
        if rover.energy < self.ENERGY_CRITICAL:
            if at_base:
                return Action.RECHARGE
            return next_step_toward(terrain, (rover.x, rover.y), (base.x, base.y))

        # 3. Damaged rover -> repair
        if rover.rover_health < self.HEALTH_DAMAGED and rover.energy > 30:
            return Action.REPAIR

        # 4. At base + energy not full -> recharge
        if at_base and rover.energy < self.ENERGY_LOW:
            return Action.RECHARGE

        # 5. Standing on uncollected science site -> collect
        site_here = self._site_here(state)
        if site_here is not None and not site_here.collected:
            if rover.has_cargo_space():
                return Action.COLLECT_SAMPLE

        # 6. Cargo full -> return home
        if not rover.has_cargo_space():
            return next_step_toward(terrain, (rover.x, rover.y), (base.x, base.y))

        # 7. Enough samples -> go home
        if rover.samples_collected >= 3:
            if not at_base:
                return next_step_toward(
                    terrain, (rover.x, rover.y), (base.x, base.y)
                )

        # 8. Otherwise -> move toward nearest uncollected site
        target = self._nearest_uncollected_site(state)
        if target is None:
            # No sites left; return to base
            if not at_base:
                return next_step_toward(
                    terrain, (rover.x, rover.y), (base.x, base.y)
                )
            return Action.WAIT

        next_action = next_step_toward(
            terrain,
            (rover.x, rover.y),
            (target.x, target.y),
        )

        # If BFS says WAIT (target unreachable), fall back to return-to-base.
        if next_action == Action.WAIT and not at_base:
            return next_step_toward(
                terrain, (rover.x, rover.y), (base.x, base.y)
            )

        return next_action

    # ---- helpers ----

    def _site_here(self, state: MissionState) -> ScienceSite | None:
        for s in state.science_sites:
            if (s.x, s.y) == (state.rover.x, state.rover.y):
                return s
        return None

    def _nearest_uncollected_site(self, state: MissionState) -> ScienceSite | None:
        remaining = [s for s in state.science_sites if not s.collected]
        if not remaining:
            return None
        rx, ry = state.rover.x, state.rover.y
        return min(remaining, key=lambda s: abs(s.x - rx) + abs(s.y - ry))