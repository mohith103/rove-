"""Abstract base class for all ROVE agents."""
from __future__ import annotations

from abc import ABC, abstractmethod

from simulation.state import MissionState


class BaseAgent(ABC):
    """Every agent (random, rule-based, RL) implements this interface."""

    name: str = "base"

    @abstractmethod
    def act(self, state: MissionState) -> int:
        """Return an action given the current mission state.

        Args:
            state: A MissionState snapshot.

        Returns:
            An integer action (see simulation.environment.Action).
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Optional hook called at the start of each mission."""
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"