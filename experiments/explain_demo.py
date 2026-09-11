"""Run a mission with the rule-based agent and print explanations.

Usage:
    python -m experiments.explain_demo
    python -m experiments.explain_demo --seed 7 --steps 20
"""
from __future__ import annotations

import argparse

from agents.commander import Commander
from agents.planner import Planner
from agents.rule_based import RuleBasedAgent
from simulation.config import load_config
from simulation.environment import MarsEnvironment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--mode", type=str, default="balanced",
                        choices=["science", "survival", "exploration", "balanced"])
    args = parser.parse_args()

    cfg = load_config()
    env = MarsEnvironment(cfg)
    state = env.reset(seed=args.seed)

    commander = Commander(
        policy=RuleBasedAgent(),
        planner=Planner(mode=args.mode),
        override_threshold=25.0,
        is_neural_net=False,
    )

    print(f"Mode: {args.mode} | Seed: {args.seed}")
    print("=" * 60)

    for i in range(args.steps):
        decision = commander.decide(state)

        print(f"\n--- SOL {state.step:03d} ---")
        print(decision.explanation.pretty())
        print("PLAN SCORES:")
        for name, score in decision.plan_scores[:3]:
            print(f"  {name:<28} {score:+.2f}")
        if decision.overridden_by_planner:
            print("  >> OVERRIDDEN BY PLANNER <<")

        state, reward, done, info = env.step(decision.action)
        print(f"  reward={reward:+.2f}  energy={state.rover.energy:.1f}  "
              f"oxygen={state.rover.oxygen:.1f}")
        if done:
            print(f"\nMission ended: success={state.success} "
                  f"reason={state.failure_reason}")
            break


if __name__ == "__main__":
    main()