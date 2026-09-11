"""Rover class for ROVE: position, resources, and consumption."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from simulation.config import ConsumptionConfig, RoverConfig


@dataclass
class Rover:
    """The ROVE Mars rover. All resources are 0-100 percentages.

    Position is set by the environment at reset time (rover deploys from base).
    `Rover.from_config` places the rover at (0, 0) as a placeholder; the
    environment immediately overwrites `.x` and `.y` with the base position.
    """

    x: int
    y: int
    energy: float
    water: float
    oxygen: float
    food: float
    battery_health: float
    rover_health: float
    communication: float = 100.0
    temperature: float = 20.0
    speed: float = 1.0
    cargo_capacity: int = 5
    samples_collected: int = 0
    cargo: list[str] = field(default_factory=list)
    current_task: str = "idle"
    status: str = "alive"

    @classmethod
    def from_config(cls, cfg: RoverConfig) -> "Rover":
        """Build a rover from config. Position is set by the environment."""
        return cls(
            x=0,  # placeholder — environment overrides with base position
            y=0,
            energy=cfg.initial_energy,
            water=cfg.initial_water,
            oxygen=cfg.initial_oxygen,
            food=cfg.initial_food,
            battery_health=cfg.initial_battery_health,
            rover_health=cfg.initial_rover_health,
            cargo_capacity=cfg.cargo_capacity,
        )

    def consume(self, key: str, amount: float) -> None:
        """Subtract from a resource, clamped to [0, 100]."""
        value = getattr(self, key)
        setattr(self, key, max(0.0, min(100.0, value - amount)))

    def restore(self, key: str, amount: float) -> None:
        """Add to a resource, clamped to [0, 100]."""
        value = getattr(self, key)
        setattr(self, key, max(0.0, min(100.0, value + amount)))

    def tick_passive(self, cons: ConsumptionConfig) -> None:
        """Per-step life support consumption and slow component wear."""
        self.consume("water", cons.water_per_tick)
        self.consume("oxygen", cons.oxygen_per_tick)
        self.consume("food", cons.food_per_tick)
        # Base wear per step
        self.consume("battery_health", cons.battery_degradation_per_tick)
        self.consume("rover_health", cons.rover_health_degradation_per_tick)

    def degrade_battery(self, amount: float) -> None:
        """Force additional battery degradation (called by events)."""
        self.consume("battery_health", amount)

    def damage_rover(self, amount: float) -> None:
        """Force additional rover damage (called by terrain/events)."""
        self.consume("rover_health", amount)

    def is_alive(self) -> bool:
        return (
            self.oxygen > 0
            and self.energy > 0
            and self.rover_health > 0
            and self.battery_health > 0
        )

    def has_cargo_space(self) -> bool:
        return len(self.cargo) < self.cargo_capacity

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": self.x, "y": self.y,
            "energy": round(self.energy, 2),
            "water": round(self.water, 2),
            "oxygen": round(self.oxygen, 2),
            "food": round(self.food, 2),
            "battery_health": round(self.battery_health, 2),
            "rover_health": round(self.rover_health, 2),
            "communication": round(self.communication, 2),
            "temperature": round(self.temperature, 2),
            "samples_collected": self.samples_collected,
            "cargo": list(self.cargo),
            "current_task": self.current_task,
            "status": self.status,
        }