"""Multi-agent commander: combines specialist proposals via weighted vote."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agents.explainer import Explanation, explain
from agents.specialists.base import Specialist, SpecialistProposal
from agents.specialists.navigation import NavigationSpecialist
from agents.specialists.resource import ResourceSpecialist
from agents.specialists.safety import SafetySpecialist
from agents.specialists.science import ScienceSpecialist
from simulation.state import MissionState


MODE_WEIGHTS: dict[str, dict[str, float]] = {
    "science": {
        "navigation": 0.7, "science": 1.5, "safety": 0.8, "resource": 0.7,
    },
    "survival": {
        "navigation": 0.8, "science": 0.5, "safety": 1.8, "resource": 1.5,
    },
    "exploration": {
        "navigation": 1.5, "science": 0.8, "safety": 0.9, "resource": 0.9,
    },
    "balanced": {
        "navigation": 1.0, "science": 1.0, "safety": 1.0, "resource": 1.0,
    },
}


@dataclass
class MultiAgentDecision:
    action: int
    explanation: Explanation
    proposals: list[SpecialistProposal] = field(default_factory=list)
    action_scores: dict[int, float] = field(default_factory=dict)
    winning_specialists: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "explanation": self.explanation.to_dict(),
            "proposals": [p.to_dict() for p in self.proposals],
            "action_scores": {str(k): round(v, 3) for k, v in self.action_scores.items()},
            "winning_specialists": self.winning_specialists,
            "multi_agent": True,
        }


class MultiAgentCommander:
    def __init__(self, mode: str = "balanced") -> None:
        if mode not in MODE_WEIGHTS:
            raise ValueError(f"unknown mode: {mode!r}")
        self.mode = mode
        self.weights = MODE_WEIGHTS[mode]
        self.specialists: list[Specialist] = [
            NavigationSpecialist(),
            ScienceSpecialist(),
            SafetySpecialist(),
            ResourceSpecialist(),
        ]

    def decide(self, state: MissionState) -> MultiAgentDecision:
        proposals = [s.propose(state) for s in self.specialists]

        scores: dict[int, float] = {}
        backers: dict[int, list[str]] = {}
        for p in proposals:
            mode_w = self.weights.get(p.specialist, 1.0)
            contribution = mode_w * p.weight
            scores[p.action] = scores.get(p.action, 0.0) + contribution
            backers.setdefault(p.action, []).append(p.specialist)

        best_action = max(
            scores.keys(),
            key=lambda a: (scores[a], len(backers[a]), -a),
        )

        explanation = explain(state, best_action, is_neural_net=False)

        return MultiAgentDecision(
            action=best_action,
            explanation=explanation,
            proposals=proposals,
            action_scores=scores,
            winning_specialists=backers[best_action],
        )
