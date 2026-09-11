#!/usr/bin/env python3
"""One-command demo for ROVE."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.commander import Commander  # noqa: E402
from agents.planner import Planner  # noqa: E402
from agents.random_agent import RandomAgent  # noqa: E402
from agents.rule_based import RuleBasedAgent  # noqa: E402
from agents.specialists.commander import MultiAgentCommander  # noqa: E402
from simulation.config import load_config_for_difficulty  # noqa: E402
from simulation.environment import MarsEnvironment  # noqa: E402
from simulation.terrain import TerrainType  # noqa: E402


GLYPHS = {
    TerrainType.PLAIN: ".",
    TerrainType.ROCK: "R",
    TerrainType.CRATER: "O",
    TerrainType.MOUNTAIN: "^",
    TerrainType.SAND: "s",
    TerrainType.BASE: "H",
    TerrainType.SCIENCE_SITE: "*",
}


def render(env: MarsEnvironment) -> str:
    assert env.terrain and env.rover and env.base
    lines = []
    for y in range(env.terrain.height):
        row = []
        for x in range(env.terrain.width):
            if (x, y) == (env.rover.x, env.rover.y):
                row.append("X")
            elif (x, y) == (env.base.x, env.base.y):
                row.append("H")
            else:
                row.append(GLYPHS[env.terrain.get(x, y)])
        lines.append(" ".join(row))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="ROVE demo")
    parser.add_argument("--difficulty", default="medium",
                        choices=["easy", "medium", "hard", "extreme"])
    parser.add_argument("--agent", default="rule_based",
                        choices=["random", "rule_based", "multi_agent"])
    parser.add_argument("--mode", default="balanced",
                        choices=["balanced", "science", "survival", "exploration"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--speed", type=float, default=0.05)
    args = parser.parse_args()

    print("=" * 60)
    print("ROVE — Autonomous Mars Mission Demo")
    print("=" * 60)
    print(f"  Difficulty : {args.difficulty}")
    print(f"  Agent      : {args.agent}")
    print(f"  Mode       : {args.mode}")
    print(f"  Seed       : {args.seed}")
    print()

    cfg = load_config_for_difficulty(args.difficulty)
    cfg.mission.max_steps = args.max_steps

    env = MarsEnvironment(cfg)
    state = env.reset(seed=args.seed)
    env.rover.x = env.base.x
    env.rover.y = env.base.y
    state = env.get_state()

    if args.agent == "random":
        policy = RandomAgent(seed=args.seed)
        commander = Commander(policy=policy, planner=Planner(mode=args.mode))
    elif args.agent == "multi_agent":
        commander = MultiAgentCommander(mode=args.mode)
    else:
        policy = RuleBasedAgent()
        commander = Commander(policy=policy, planner=Planner(mode=args.mode))

    print("Initial state:")
    print(render(env))
    print()

    start = time.time()
    steps = 0
    while not state.done:
        decision = commander.decide(state)
        state, reward, done, info = env.step(decision.action)
        steps += 1

        action_name = info.get("action", "?")
        print(f"SOL {state.step:03d} | {action_name:<16} "
              f"| energy={state.rover.energy:5.1f}% "
              f"| oxygen={state.rover.oxygen:5.1f}% "
              f"| samples={state.rover.samples_collected}")

        if args.speed > 0:
            time.sleep(args.speed)

        if steps >= args.max_steps and not state.done:
            print(f"\n--- Demo step limit reached ({args.max_steps}) ---")
            break

    elapsed = time.time() - start

    print("\nFinal state:")
    print(render(env))
    print()
    print("=" * 60)
    print(f"Mission result   : {'SUCCESS' if state.success else 'FAILED'}")
    print(f"Reason           : {state.failure_reason or '(completed)'}")
    print(f"Samples collected: {state.rover.samples_collected}")
    print(f"Steps taken      : {state.step}")
    print(f"Energy left      : {state.rover.energy:.1f}%")
    print(f"Oxygen left      : {state.rover.oxygen:.1f}%")
    print(f"Wall-clock time  : {elapsed:.2f}s")
    print("=" * 60)

    return 0 if state.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
