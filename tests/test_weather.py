"""Tests for the weather system."""
from __future__ import annotations

import numpy as np

from simulation.weather import Weather, WeatherType, WEATHER_EFFECTS


def make_weather(prob_dust_storm: float = 0.0) -> Weather:
    cfg = {
        "change_probability": 0.0,
        "probabilities": {
            "clear": 1.0 - prob_dust_storm,
            "dusty": 0.0,
            "dust_storm": prob_dust_storm,
            "cold_snap": 0.0,
            "extreme_cold": 0.0,
        },
        "duration": {"clear": [1, 1], "moderate": [5, 5], "severe": [10, 10]},
    }
    return Weather(cfg, np.random.default_rng(0))


def test_starts_clear():
    w = make_weather()
    assert w.current == WeatherType.CLEAR


def test_dust_storm_reduces_solar():
    w = make_weather(prob_dust_storm=1.0)
    w._sample_weather = lambda: (WeatherType.DUST_STORM, 10)  # force
    w.weather_cfg["change_probability"] = 1.0
    w.step()
    assert w.current == WeatherType.DUST_STORM
    assert w.effects().solar_multiplier < 1.0


def test_duration_ticks_down():
    w = make_weather(prob_dust_storm=1.0)
    w.current = WeatherType.DUST_STORM
    w.remaining_steps = 3
    w.step()
    assert w.remaining_steps == 2
    w.step()
    assert w.remaining_steps == 1


def test_weather_effects_defined_for_all():
    for wt in WeatherType:
        assert wt in WEATHER_EFFECTS