"""Weather system for ROVE: dust storms, cold snaps, and clear skies."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import numpy as np


class WeatherType(IntEnum):
    CLEAR = 0
    DUSTY = 1
    DUST_STORM = 2
    COLD_SNAP = 3
    EXTREME_COLD = 4


WEATHER_NAMES: dict[WeatherType, str] = {
    WeatherType.CLEAR: "clear",
    WeatherType.DUSTY: "dusty",
    WeatherType.DUST_STORM: "dust_storm",
    WeatherType.COLD_SNAP: "cold_snap",
    WeatherType.EXTREME_COLD: "extreme_cold",
}


@dataclass
class WeatherEffects:
    """Multipliers and deltas applied while a weather is active."""
    solar_multiplier: float = 1.0     # scales energy generation
    move_cost_multiplier: float = 1.0 # scales movement cost
    temperature_delta: float = 0.0    # added to rover.temperature
    comms_delta: float = 0.0          # subtracted from rover.communication


WEATHER_EFFECTS: dict[WeatherType, WeatherEffects] = {
    WeatherType.CLEAR: WeatherEffects(),
    WeatherType.DUSTY: WeatherEffects(solar_multiplier=0.85, move_cost_multiplier=1.1),
    WeatherType.DUST_STORM: WeatherEffects(
        solar_multiplier=0.42, move_cost_multiplier=1.5, comms_delta=15.0
    ),
    WeatherType.COLD_SNAP: WeatherEffects(
        solar_multiplier=0.9, move_cost_multiplier=1.2, temperature_delta=-25.0
    ),
    WeatherType.EXTREME_COLD: WeatherEffects(
        solar_multiplier=0.8, move_cost_multiplier=1.4, temperature_delta=-55.0
    ),
}


@dataclass
class Weather:
    """Tracks the current weather and transitions.

    Weather transitions occur probabilistically each step. A weather
    system also stores a duration so storms feel like episodes, not noise.
    """

    weather_cfg: dict
    rng: np.random.Generator
    current: WeatherType = WeatherType.CLEAR
    remaining_steps: int = 0

    def step(self) -> None:
        """Advance the weather one simulation step."""
        if self.remaining_steps > 0:
            self.remaining_steps -= 1
            return

        # Try to start new weather
        if self.rng.random() < self.weather_cfg.get("change_probability", 0.02):
            new_weather, duration = self._sample_weather()
            self.current = new_weather
            self.remaining_steps = duration

    def _sample_weather(self) -> tuple[WeatherType, int]:
        probs = self.weather_cfg.get("probabilities", {})
        names = ["clear", "dusty", "dust_storm", "cold_snap", "extreme_cold"]
        weights = [probs.get(n, 0.0) for n in names]
        total = sum(weights) or 1.0
        weights = [w / total for w in weights]

        idx = int(self.rng.choice(len(names), p=weights))
        weather = WeatherType(idx)

        duration_range = self.weather_cfg.get("duration", {})
        if weather == WeatherType.CLEAR:
            low, high = duration_range.get("clear", [1, 5])
        elif weather in (WeatherType.DUSTY, WeatherType.COLD_SNAP):
            low, high = duration_range.get("moderate", [5, 15])
        else:
            low, high = duration_range.get("severe", [10, 25])

        duration = int(self.rng.integers(low, high + 1))
        return weather, duration

    def effects(self) -> WeatherEffects:
        return WEATHER_EFFECTS[self.current]

    def reset(self) -> None:
        self.current = WeatherType.CLEAR
        self.remaining_steps = 0

    def to_dict(self) -> dict:
        return {
            "type": WEATHER_NAMES[self.current],
            "remaining_steps": self.remaining_steps,
            "solar_multiplier": self.effects().solar_multiplier,
            "move_cost_multiplier": self.effects().move_cost_multiplier,
            "temperature_delta": self.effects().temperature_delta,
        }