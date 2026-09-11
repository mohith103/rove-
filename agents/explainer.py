"""Post-hoc explanation engine for ROVE decisions.

IMPORTANT HONESTY NOTE
----------------------
The explanation is generated *after* the action is chosen. It analyzes the
state and the action, and produces a human-readable summary. It does NOT
reflect the internal activations of a neural network. This is intentional
and clearly labeled in the output via `is_from_neural_net`.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from simulation.environment import Action
from simulation.events import EventType
from simulation.state import MissionState
from simulation.weather import WeatherType


@dataclass
class Explanation:
    action: int
    action_name: str
    reason: str
    factors: dict[str, str]
    confidence: float
    risk_estimate: float
    is_from_neural_net: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def pretty(self) -> str:
        lines = [
            f"DECISION: {self.action_name}",
            "FACTORS:",
        ]
        for k, v in self.factors.items():
            lines.append(f"  {k:<22} {v}")
        lines.append(f"REASON: {self.reason}")
        lines.append(f"CONFIDENCE: {self.confidence:.2f}")
        lines.append(f"RISK ESTIMATE: {self.risk_estimate:.2f}")
        if self.is_from_neural_net:
            lines.append("(Explanation generated post-hoc; policy is a neural net.)")
        return "\n".join(lines)


# -----------------------------------------------------------------------------
# Heuristic confidence per action type
# -----------------------------------------------------------------------------

def _confidence_for(action: int, state: MissionState) -> float:
    """Return a heuristic confidence in [0, 1].

    High confidence when the action is clearly forced by state
    (e.g., low oxygen → return). Low when the state is ambiguous.
    """
    r = state.rover
    if action == Action.RETURN_TO_BASE:
        # Very confident if oxygen or energy is critical
        if r.oxygen < 20 or r.energy < 15:
            return 0.95
        if r.oxygen < 40 or r.energy < 30:
            return 0.75
        return 0.55
    if action == Action.RECHARGE:
        if (r.x, r.y) == (state.base.x, state.base.y) and r.energy < 50:
            return 0.95
        return 0.6
    if action == Action.COLLECT_SAMPLE:
        # Confident if standing on an uncollected site
        for s in state.science_sites:
            if (s.x, s.y) == (r.x, r.y) and not s.collected:
                return 0.9
        return 0.3
    if action == Action.REPAIR:
        return 0.85 if r.rover_health < 50 else 0.5
    if action in (Action.MOVE_NORTH, Action.MOVE_SOUTH,
                  Action.MOVE_EAST, Action.MOVE_WEST):
        return 0.6
    if action == Action.WAIT:
        return 0.4
    return 0.5


def _risk_estimate(state: MissionState) -> float:
    """Return a risk estimate in [0, 1] based on resources and environment."""
    r = state.rover
    risk = 0.0

    # Resource risk
    risk += max(0.0, (30 - r.energy) / 30) * 0.35
    risk += max(0.0, (40 - r.oxygen) / 40) * 0.30
    risk += max(0.0, (60 - r.rover_health) / 60) * 0.15
    risk += max(0.0, (80 - r.battery_health) / 80) * 0.10

    # Distance risk
    d = abs(r.x - state.base.x) + abs(r.y - state.base.y)
    risk += min(1.0, d / 30) * 0.10

    return min(1.0, risk)


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

def explain(
    state: MissionState,
    action: int,
    is_neural_net: bool = False,
) -> Explanation:
    """Produce an Explanation for the given action and state."""
    r = state.rover
    factors: dict[str, str] = {}

    # Always include these
    factors["energy"] = f"{r.energy:5.1f}%"
    factors["oxygen"] = f"{r.oxygen:5.1f}%"
    factors["rover_health"] = f"{r.rover_health:5.1f}%"
    factors["distance_to_base"] = f"{abs(r.x - state.base.x) + abs(r.y - state.base.y)}"
    factors["samples_collected"] = f"{r.samples_collected}/{state.max_steps // 66}"

    # Weather and failures (if present)
    weather_name = "unknown"
    if hasattr(state, "weather") and state.weather is not None:  # not always present
        weather_name = state.weather.type.name.lower()
    factors["weather"] = weather_name

    # Reason text depends on the action
    reason = _reason_for(action, state)

    confidence = _confidence_for(action, state)
    risk = _risk_estimate(state)

    return Explanation(
        action=action,
        action_name=Action.NAMES.get(action, f"UNKNOWN({action})"),
        reason=reason,
        factors=factors,
        confidence=confidence,
        risk_estimate=risk,
        is_from_neural_net=is_neural_net,
    )


def _reason_for(action: int, state: MissionState) -> str:
    r = state.rover
    if action == Action.RETURN_TO_BASE:
        if r.oxygen < 25:
            return "Oxygen is critically low; returning to base is the safest action."
        if r.energy < 20:
            return "Energy reserve is insufficient for further exploration."
        if not r.has_cargo_space():
            return "Cargo is full; returning to base to unload."
        return "Returning to base as a precaution."
    if action == Action.RECHARGE:
        return "Recharging at base to restore energy reserves."
    if action == Action.COLLECT_SAMPLE:
        return "Standing on an uncollected scientific site; collecting the sample."
    if action == Action.ANALYZE_SAMPLE:
        return "Analyzing collected samples for additional scientific value."
    if action == Action.REPAIR:
        return "Rover health is degraded; performing repairs."
    if action == Action.COMMUNICATE:
        return "Restoring communication with mission control."
    if action == Action.WAIT:
        return "Waiting to conserve resources before the next move."
    if action in (Action.MOVE_NORTH, Action.MOVE_SOUTH,
                  Action.MOVE_EAST, Action.MOVE_WEST):
        return "Navigating toward the next objective."
    return "No specific rationale available."