"""Science specialist: maximizes sample collection."""
from __future__ import annotations

from agents.specialists.base import Specialist, SpecialistProposal
from simulation.environment import Action
from simulation.state import MissionState


class ScienceSpecialist(Specialist):
    name = "science"

    def propose(self, state: MissionState) -> SpecialistProposal:
        rover = state.rover

        for site in state.science_sites:
            if (site.x, site.y) == (rover.x, rover.y) and not site.collected:
                if rover.has_cargo_space():
                    return SpecialistProposal(
                        specialist=self.name,
                        action=Action.COLLECT_SAMPLE,
                        weight=0.95,
                        rationale=f"Collect sample worth {site.value}.",
                    )
                return SpecialistProposal(
                    specialist=self.name,
                    action=Action.RETURN_TO_BASE,
                    weight=0.85,
                    rationale="Cargo full; unload at base to collect more.",
                )

        if not rover.has_cargo_space():
            return SpecialistProposal(
                specialist=self.name,
                action=Action.RETURN_TO_BASE,
                weight=0.75,
                rationale="Cargo full; return to base to unload.",
            )

        return SpecialistProposal(
            specialist=self.name,
            action=Action.WAIT,
            weight=0.15,
            rationale="No immediate science opportunity.",
        )
