"""Base station for ROVE."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BaseStation:
    """The Mars base. Rover can recharge here."""

    x: int
    y: int
    recharge_rate: float = 10.0

    def distance_to(self, x: int, y: int) -> float:
        return abs(self.x - x) + abs(self.y - y)

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "recharge_rate": self.recharge_rate}