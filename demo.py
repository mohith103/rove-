"""Manual demo: watch RandomAgent or RuleBasedAgent explore Mars."""
from __future__ import annotations

import sys

from agents.base_agent import BaseAgent
from agents.random_agent import RandomAgent
from agents.rule_based import RuleBasedAgent
from simulation.environment import MarsEnvironment
from simulation.terrain import TerrainType

GLYPH = {
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
    lines: list[str] = []
    for y in range(env.terrain.height):
        row: list[str] = []
        for x in range(env.terrain.width):
            if (x, y) == (env.rover.x, env.rover.y):
                row.append("X")
            elif (x, y) == (env.base.x, env.base.y):
                row.append("H")
            else:
                t = env.terrain.get(x, y)
                row.append(GLYPH[t])
        lines.append(" ".join(row))
    return "\n".join(lines)


def pick_agent(name: str) -> BaseAgent:
    if name == "random":
        return RandomAgent(seed=7)
    if name == "rule":
        return RuleBasedAgent()
    raise ValueError(f"unknown agent: {name}")


def main() -> None:
    agent_name = sys.argv[1] if len(sys.argv) > 1 else "rule"
    agent = pick_agent(agent_name)

    env = MarsEnvironment()
    state = env.reset(seed=42)

    print(f"Agent: {agent.name}")
    print("Initial state:")
    print(render(env))
    print()

    for _ in range(60):
        action = agent.act(state)
        state, reward, done, info = env.step(action)
        print(f"SOL {state.step:03d} | {info['action']:<16} "
              f"r={reward:+7.2f} E={state.rover.energy:5.1f} "
              f"O2={state.rover.oxygen:5.1f} samples={state.rover.samples_collected}")
        if done:
            break

    print("\nFinal state:")
    print(render(env))
    print()
    print(f"Done: {state.done}  Success: {state.success}  Reason: {state.failure_reason}")
    print(f"Samples collected: {state.rover.samples_collected}")
    print(f"Steps taken: {state.step}")


if __name__ == "__main__":
    main()