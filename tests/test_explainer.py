"""Tests for the explanation engine."""
from __future__ import annotations

from agents.explainer import Explanation, explain, _risk_estimate
from simulation.environment import Action, MarsEnvironment


def test_explain_returns_explanation():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    exp = explain(state, Action.RETURN_TO_BASE)
    assert isinstance(exp, Explanation)
    assert exp.action == Action.RETURN_TO_BASE
    assert exp.action_name == "RETURN_TO_BASE"


def test_explanation_has_required_factors():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    exp = explain(state, Action.WAIT)
    for key in ["energy", "oxygen", "rover_health", "distance_to_base"]:
        assert key in exp.factors


def test_confidence_is_bounded():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    for action in range(11):
        exp = explain(state, action)
        assert 0.0 <= exp.confidence <= 1.0
        assert 0.0 <= exp.risk_estimate <= 1.0


def test_low_oxygen_gives_high_confidence_return():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    state.rover.oxygen = 10.0
    exp = explain(state, Action.RETURN_TO_BASE)
    assert exp.confidence >= 0.9


def test_risk_increases_when_resources_low():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    baseline = _risk_estimate(state)
    state.rover.energy = 5.0
    state.rover.oxygen = 5.0
    assert _risk_estimate(state) > baseline


def test_pretty_output_contains_key_phrases():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    text = explain(state, Action.WAIT).pretty()
    assert "DECISION:" in text
    assert "FACTORS:" in text
    assert "REASON:" in text
    assert "CONFIDENCE:" in text