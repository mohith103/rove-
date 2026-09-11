"""Mission state snapshot for ROVE."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from simulation.base import BaseStation
from simulation.rover import Rover
from simulation.terrain import Terrain


@dataclass
class ScienceSite:
    """A scientific objective location."""
    x: int
    y: int
    value: int
    difficulty: int
    sample_type: str
    collected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": self.x, "y": self.y,
            "value": self.value,
            "difficulty": self.difficulty,
            "sample_type": self.sample_type,
            "collected": self.collected,
        }


@dataclass
class MissionState:
    """Complete state of a ROVE mission at one tick."""

    step: int
    max_steps: int
    terrain: Terrain
    rover: Rover
    base: BaseStation
    science_sites: list[ScienceSite]
    done: bool = False
    success: bool = False
    failure_reason: str | None = None
    events_log: list[str] = field(default_factory=list)

    def add_event(self, message: str) -> None:
        self.events_log.append(f"[SOL {self.step:03d}] {message}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "max_steps": self.max_steps,
            "rover": self.rover.to_dict(),
            "base": self.base.to_dict(),
            "science_sites": [s.to_dict() for s in self.science_sites],
            "done": self.done,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "events": self.events_log[-20:],
        }