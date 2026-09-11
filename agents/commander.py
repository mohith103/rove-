"""The ROVE Commander: wraps a base policy with explainer + planner.

Design
------
The Commander is the top-level decision interface. It:
  1. Asks the base policy for an action.
  2. Asks the planner for its preferred plan.
  3. Applies a hard safety layer (survival overrides everything).
  4. Applies a soft override when the planner is confident.
  5. Generates an explanation for the chosen action.

This separates *policy* (what to do) from *explanation* (why) and
*planning* (advice). Each component is testable in isolation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from agents.base_agent import BaseAgent
from agents.explainer import Explanation, explain
from agents.planner import Plan, Planner
from simulation.environment import Action
from simulation.state import MissionState


class Policy(Protocol):
    """Anything with .act(state) -> int can be used as a policy."""
    def act(self, state: MissionState) -> int: ...


@dataclass
class CommanderDecision:
    action: int
    explanation: Explanation
    chosen_plan: Plan | None
    plan_scores: list[tuple[str, float]]
    overridden_by_planner: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "explanation": self.explanation.to_dict(),
            "chosen_plan": self.chosen_plan.to_dict() if self.chosen_plan else None,
            "plan_scores": self.plan_scores,
            "overridden_by_planner": self.overridden_by_planner,
        }


class Commander:
    """Unified decision interface for ROVE."""

    def __init__(
        self,
        policy: Policy | BaseAgent,
        planner: Planner | None = None,
        override_threshold: float = 25.0,
        is_neural_net: bool = False,
    ) -> None:
        """
        Args:
            policy: base policy (rule-based or PPO). Must have .act(state).
            planner: optional planner. Defaults to a balanced planner.
            override_threshold: minimum score gap between the planner's top
                plan and its runner-up before the planner may override the
                policy. Higher = stricter (less overriding).
            is_neural_net: if True, mark explanations as post-hoc.
        """
        self.policy = policy
        self.planner = planner or Planner(mode="balanced")
        self.override_threshold = override_threshold
        self.is_neural_net = is_neural_net

    # ------------------------------------------------------------------ #

    def decide(self, state: MissionState) -> CommanderDecision:
        # 1. Ask policy
        policy_action = self.policy.act(state)

        # 2. Ask planner
        best_plan, scored = self.planner.choose(state)
        plan_scores = [(p.name, s) for p, s in scored]

        # 3. Safety layer (highest priority) -- hard rules
        action = policy_action
        overridden = False

        r = state.rover
        at_base = (r.x, r.y) == (state.base.x, state.base.y)

        if not at_base and (r.oxygen < 20.0 or r.energy < 15.0):
            # Critical resources -> force return, no questions asked.
            action = Action.RETURN_TO_BASE
            overridden = (policy_action != Action.RETURN_TO_BASE)

        elif at_base and r.energy < 50.0 and policy_action != Action.RECHARGE:
            # At base with low energy -> force recharge.
            action = Action.RECHARGE
            overridden = True

        elif (
            best_plan.action == Action.RETURN_TO_BASE
            and policy_action != Action.RETURN_TO_BASE
            and self._plan_margin(scored) >= self.override_threshold
        ):
            # Softer override: planner strongly prefers home over its runner-up.
            action = best_plan.action
            overridden = True

        # 4. Explain
        explanation = explain(state, action, is_neural_net=self.is_neural_net)

        return CommanderDecision(
            action=action,
            explanation=explanation,
            chosen_plan=best_plan,
            plan_scores=plan_scores,
            overridden_by_planner=overridden,
        )

    # ------------------------------------------------------------------ #

    @staticmethod
    def _plan_margin(scored: list[tuple[Plan, float]]) -> float:
        """Return how much the best plan beats the runner-up.

        A small margin means the planner is not very confident; a large
        margin means the planner strongly prefers the top plan.
        """
        if len(scored) < 2:
            return float("inf")
        return scored[0][1] - scored[1][1]

    @staticmethod
    def _risk_of(state: MissionState) -> float:
        """Convenience: expose the explainer's risk estimator."""
        from agents.explainer import _risk_estimate
        return _risk_estimate(state)