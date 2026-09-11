"""Tests for the planner."""
from __future__ import annotations

from agents.planner import Planner, Plan, MODE_PRESETS
from simulation.environment import Action, MarsEnvironment


def test_balanced_planner_picks_something():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    planner = Planner(mode="balanced")
    best, scored = planner.choose(state)
    assert isinstance(best, Plan)
    assert len(scored) >= 2  # at least return_to_base + visit_site


def test_low_energy_survival_mode_prefers_return():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    state.rover.energy = 10.0
    state.rover.x, state.rover.y = 8, 8

    survival = Planner(mode="survival")
    best, _ = survival.choose(state)
    assert best.action == Action.RETURN_TO_BASE


def test_science_mode_picks_site_when_healthy():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    state.rover.energy = 95.0
    state.rover.oxygen = 95.0

    science = Planner(mode="science")
    best, _ = science.choose(state)
    # Should pick a science plan, not return_to_base
    assert best.action != Action.RETURN_TO_BASE


def test_unknown_mode_raises():
    import pytest
    with pytest.raises(ValueError):
        Planner(mode="nonsense")


def test_all_mode_presets_load():
    for name in MODE_PRESETS:
        Planner(mode=name)