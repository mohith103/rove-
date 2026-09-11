"""Random events for ROVE: equipment failures and anomalies."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

import numpy as np


class EventType(IntEnum):
    NONE = 0
    SOLAR_PANEL_FAILURE = 1
    WHEEL_FAILURE = 2
    BATTERY_DEGRADATION = 3
    COMMUNICATION_LOSS = 4
    NAVIGATION_SENSOR_FAILURE = 5
    WATER_LEAK = 6
    ROVER_OVERHEATING = 7


EVENT_NAMES: dict[EventType, str] = {
    EventType.NONE: "none",
    EventType.SOLAR_PANEL_FAILURE: "solar_panel_failure",
    EventType.WHEEL_FAILURE: "wheel_failure",
    EventType.BATTERY_DEGRADATION: "battery_degradation",
    EventType.COMMUNICATION_LOSS: "communication_loss",
    EventType.NAVIGATION_SENSOR_FAILURE: "navigation_sensor_failure",
    EventType.WATER_LEAK: "water_leak",
    EventType.ROVER_OVERHEATING: "rover_overheating",
}


@dataclass
class ActiveFailure:
    """A currently-active failure with duration and effects."""
    type: EventType
    duration: int
    severity: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": EVENT_NAMES[self.type],
            "duration": self.duration,
            "severity": round(self.severity, 3),
        }


@dataclass
class EventEngine:
    """Rolls for new events each step and ticks down existing ones.

    An event's severity ranges [0, 1]. Higher = worse.
    Effects are applied by the environment, not by this class.
    """
    config: dict
    rng: np.random.Generator
    active: list[ActiveFailure] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    def step(self, step: int) -> list[ActiveFailure]:
        """Advance events one step. Returns list of newly-started failures."""
        # Tick down existing
        still_active: list[ActiveFailure] = []
        for f in self.active:
            f.duration -= 1
            if f.duration > 0:
                still_active.append(f)
        self.active = still_active

        # Roll for new
        new_failures: list[ActiveFailure] = []
        base_prob = self.config.get("base_probability", 0.01)
        if self.rng.random() < base_prob:
            event_type = self._sample_event()
            if event_type != EventType.NONE:
                # Don't duplicate an active failure
                if not any(f.type == event_type for f in self.active):
                    severity = float(self.rng.uniform(0.3, 1.0))
                    duration = int(self.rng.integers(5, 20))
                    f = ActiveFailure(event_type, duration, severity)
                    self.active.append(f)
                    new_failures.append(f)
                    self.log.append(
                        f"[SOL {step:03d}] EVENT: {EVENT_NAMES[event_type]} "
                        f"(dur={duration}, sev={severity:.2f})"
                    )
        return new_failures

    def _sample_event(self) -> EventType:
        probs = self.config.get("probabilities", {})
        names = [
            "solar_panel_failure", "wheel_failure", "battery_degradation",
            "communication_loss", "navigation_sensor_failure",
            "water_leak", "rover_overheating",
        ]
        weights = [probs.get(n, 0.0) for n in names]
        total = sum(weights)
        if total <= 0:
            return EventType.NONE
        weights = [w / total for w in weights]
        idx = int(self.rng.choice(len(names), p=weights))
        return EventType(idx + 1)  # +1 because NONE is 0

    # ---- Query helpers ----

    def has(self, etype: EventType) -> bool:
        return any(f.type == etype for f in self.active)

    def severity_of(self, etype: EventType) -> float:
        for f in self.active:
            if f.type == etype:
                return f.severity
        return 0.0

    def solar_multiplier(self) -> float:
        if self.has(EventType.SOLAR_PANEL_FAILURE):
            return 1.0 - 0.6 * self.severity_of(EventType.SOLAR_PANEL_FAILURE)
        return 1.0

    def move_cost_multiplier(self) -> float:
        if self.has(EventType.WHEEL_FAILURE):
            return 1.0 + 1.5 * self.severity_of(EventType.WHEEL_FAILURE)
        return 1.0

    def water_drain_bonus(self) -> float:
        if self.has(EventType.WATER_LEAK):
            return 0.5 * self.severity_of(EventType.WATER_LEAK)
        return 0.0

    def temperature_delta(self) -> float:
        if self.has(EventType.ROVER_OVERHEATING):
            return 30.0 * self.severity_of(EventType.ROVER_OVERHEATING)
        return 0.0

    def navigation_blind(self) -> bool:
        return self.has(EventType.NAVIGATION_SENSOR_FAILURE)

    def comms_lost(self) -> bool:
        return self.has(EventType.COMMUNICATION_LOSS)

    def reset(self) -> None:
        self.active = []
        self.log = []