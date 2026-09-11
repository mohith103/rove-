"""Safety specialist: prevents catastrophic failures."""
from __future__ import annotations

from agents.specialists.base import Specialist, SpecialistProposal
from simulation.environment import Action
from simulation.state import MissionState


class SafetySpecialist(Specialist):
    name = "safety"

    OXYGEN_CRITICAL = 25.0
    ENERGY_CRITICAL = 20.0
    ENERGY_LOW = 60.0
    HEALTH_LOW = 50.0

    def propose(self, state: MissionState) -> SpecialistProposal:
        rover = state.rover
        base = state.base
        at_base = (rover.x, rover.y) == (base.x, base.y)

        if rover.oxygen < self.OXYGEN_CRITICAL and not at_base:
            return SpecialistProposal(
                specialist=self.name,
                action=Action.RETURN_TO_BASE,
                weight=0.95,
                rationale=f"Oxygen at {rover.oxygen:.1f}% — critical.",
            )

        if rover.energy < self.ENERGY_CRITICAL and not at_base:
            return SpecialistProposal(
                specialist=self.name,
                action=Action.RETURN_TO_BASE,
                weight=0.95,
                rationale=f"Energy at {rover.energy:.1f}% — critical.",
            )

        if at_base and rover.energy < self.ENERGY_LOW:
            return SpecialistProposal(
                specialist=self.name,
                action=Action.RECHARGE,
                weight=0.9,
                rationale=f"At base, energy {rover.energy:.1f}% — recharge.",
            )

        if rover.rover_health < self.HEALTH_LOW:
            return SpecialistProposal(
                specialist=self.name,
                action=Action.REPAIR,
                weight=0.75,
                rationale=f"Rover health at {rover.rover_health:.1f}% — repair.",
            )

        return SpecialistProposal(
            specialist=self.name,
            action=Action.WAIT,
            weight=0.15,
            rationale="No safety concerns.",
        )
