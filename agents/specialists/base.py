"""Base classes for specialist agents."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from simulation.state import MissionState


@dataclass
class SpecialistProposal:
    """A specialist's suggestion for the next action."""
    specialist: str
    action: int
    weight: float
    rationale: str

    def to_dict(self) -> dict:
        return {
            "specialist": self.specialist,
            "action": self.action,
            "weight": round(self.weight, 3),
            "rationale": self.rationale,
        }


class Specialist(ABC):
    """A single specialist. Each one proposes exactly one action per step."""

    name: str = "specialist"

    @abstractmethod
    def propose(self, state: MissionState) -> SpecialistProposal:
        raise NotImplementedError
