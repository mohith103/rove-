"""Tests for the event engine."""
from __future__ import annotations

import numpy as np

from simulation.events import EventEngine, EventType, ActiveFailure


def make_engine(prob: float = 0.0) -> EventEngine:
    cfg = {
        "base_probability": prob,
        "probabilities": {
            "solar_panel_failure": 1.0,
            "wheel_failure": 0.0,
            "battery_degradation": 0.0,
            "communication_loss": 0.0,
            "navigation_sensor_failure": 0.0,
            "water_leak": 0.0,
            "rover_overheating": 0.0,
        },
    }
    return EventEngine(cfg, np.random.default_rng(0))


def test_no_events_when_prob_zero():
    e = make_engine(prob=0.0)
    for i in range(100):
        new = e.step(i)
    assert e.active == []


def test_event_fires_when_prob_one():
    e = make_engine(prob=1.0)
    new = e.step(0)
    assert len(new) == 1
    assert new[0].type == EventType.SOLAR_PANEL_FAILURE


def test_event_expires():
    # Fire once, then set probability to 0 so no new events spawn
    e = make_engine(prob=1.0)
    new = e.step(0)
    assert len(new) == 1
    dur = new[0].duration

    # Prevent respawning
    e.config["base_probability"] = 0.0

    # Advance enough steps to fully expire
    for i in range(1, dur + 2):
        e.step(i)

    assert e.active == []


def test_solar_multiplier_reflects_severity():
    e = make_engine(prob=0.0)
    e.active.append(ActiveFailure(EventType.SOLAR_PANEL_FAILURE, 5, 0.5))
    assert e.solar_multiplier() < 1.0
    assert 0.0 < e.solar_multiplier() <= 1.0