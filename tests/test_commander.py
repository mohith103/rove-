"""Tests for the Commander."""
from __future__ import annotations

import pytest

from agents.commander import Commander, CommanderDecision
from agents.planner import Planner
from agents.rule_based import RuleBasedAgent
from simulation.environment import Action, MarsEnvironment


def test_commander_returns_decision():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    cmd = Commander(policy=RuleBasedAgent())
    d = cmd.decide(state)
    assert isinstance(d, CommanderDecision)
    assert 0 <= d.action < 11
    assert d.explanation is not None


def test_commander_defers_to_policy_when_healthy():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    # Set up so rule-based would collect a sample
    site = state.science_sites[0]
    state.rover.x, state.rover.y = site.x, site.y
    state.rover.energy = 90.0
    state.rover.oxygen = 90.0

    cmd = Commander(policy=RuleBasedAgent())
    d = cmd.decide(state)
    assert d.action == Action.COLLECT_SAMPLE
    assert d.overridden_by_planner is False


def test_commander_overrides_to_return_when_critical():
    """Hard safety layer: critical oxygen/energy forces RETURN_TO_BASE."""
    env = MarsEnvironment()
    state = env.reset(seed=42)
    # Rover far from base, critical resources
    state.rover.x, state.rover.y = 10, 10
    state.rover.energy = 12.0
    state.rover.oxygen = 12.0

    # A policy that always moves east would be overridden
    class MoveEast:
        name = "move_east"
        def act(self, s):
            return Action.MOVE_EAST
        def reset(self):
            pass

    cmd = Commander(policy=MoveEast(), override_threshold=1.0)
    d = cmd.decide(state)
    assert d.action == Action.RETURN_TO_BASE
    assert d.overridden_by_planner is True


def test_commander_soft_override_when_risk_high_and_planner_agrees():
    """When risk > 0.6 and the planner picks return-to-base, override the policy.

    Setup: rover far from base with low-ish resources, but above the
    hard safety thresholds. A survival-mode planner should prefer
    return_to_base, and the Commander should override the policy.
    """
    env = MarsEnvironment()
    state = env.reset(seed=42)

    # Far from base, low-ish resources (but above safety thresholds)
    state.rover.x, state.rover.y = 12, 12
    state.rover.energy = 22.0         # above 15% safety threshold
    state.rover.oxygen = 28.0         # above 20% safety threshold
    state.rover.rover_health = 100.0  # healthy -> no repair plan
    state.rover.battery_health = 100.0

    class MoveEast:
        name = "move_east"
        def act(self, s):
            return Action.MOVE_EAST
        def reset(self):
            pass

    # Use a survival-mode planner so return_to_base wins
    safety_planner = Planner(mode="survival")

    cmd = Commander(
        policy=MoveEast(),
        planner=safety_planner,
        override_threshold=1.0,
    )
    d = cmd.decide(state)

    # Confirm the planner actually prefers return_to_base
    planner_choice = d.chosen_plan.action
    assert planner_choice == Action.RETURN_TO_BASE, (
        f"planner picked {planner_choice}, expected RETURN_TO_BASE; "
        f"plan_scores={d.plan_scores}"
    )

    # And the Commander should have overridden MoveEast
    assert d.action == Action.RETURN_TO_BASE
    assert d.overridden_by_planner is True


def test_decision_serializes():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    cmd = Commander(policy=RuleBasedAgent())
    d = cmd.decide(state)
    payload = d.to_dict()
    assert "action" in payload
    assert "explanation" in payload
    assert "plan_scores" in payload