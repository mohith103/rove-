"""Run N missions per agent and compare them on real metrics.

Usage:
    python -m experiments.baseline --episodes 100
    python -m experiments.baseline --episodes 500 --seed 7
"""
from __future__ import annotations

import argparse
import csv
import statistics
from dataclasses import dataclass, asdict
from pathlib import Path

from agents.base_agent import BaseAgent
from agents.random_agent import RandomAgent
from agents.rule_based import RuleBasedAgent
from simulation.environment import MarsEnvironment


@dataclass
class EpisodeResult:
    agent: str
    seed: int
    success: bool
    samples: int
    steps: int
    energy_left: float
    oxygen_left: float
    failure_reason: str | None


@dataclass
class AgentSummary:
    agent: str
    episodes: int
    success_rate: float
    avg_samples: float
    avg_steps: float
    avg_energy_left: float
    avg_oxygen_left: float
    top_failure: str


def make_agent(name: str, seed: int) -> BaseAgent:
    if name == "random":
        return RandomAgent(seed=seed)
    if name == "rule_based":
        return RuleBasedAgent()
    raise ValueError(f"unknown agent: {name}")


def run_episode(agent: BaseAgent, env: MarsEnvironment, seed: int) -> EpisodeResult:
    agent.reset()
    state = env.reset(seed=seed)
    done = False
    while not done and state.step < env.cfg.mission.max_steps * 2:
        action = agent.act(state)
        state, _, done, _ = env.step(action)
    return EpisodeResult(
        agent=agent.name,
        seed=seed,
        success=state.success,
        samples=state.rover.samples_collected,
        steps=state.step,
        energy_left=state.rover.energy,
        oxygen_left=state.rover.oxygen,
        failure_reason=state.failure_reason,
    )


def summarize(results: list[EpisodeResult]) -> AgentSummary:
    if not results:
        raise ValueError("no results")
    n = len(results)
    reasons = [r.failure_reason for r in results if r.failure_reason]
    top_failure = statistics.mode(reasons) if reasons else "none"
    return AgentSummary(
        agent=results[0].agent,
        episodes=n,
        success_rate=sum(1 for r in results if r.success) / n,
        avg_samples=sum(r.samples for r in results) / n,
        avg_steps=sum(r.steps for r in results) / n,
        avg_energy_left=sum(r.energy_left for r in results) / n,
        avg_oxygen_left=sum(r.oxygen_left for r in results) / n,
        top_failure=top_failure,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=100,
                        help="episodes per agent")
    parser.add_argument("--seed", type=int, default=0,
                        help="base seed for episode generation")
    parser.add_argument("--agents", nargs="+",
                        default=["random", "rule_based"],
                        help="which agents to run")
    parser.add_argument("--out", type=str,
                        default="experiments/results/baseline.csv",
                        help="output CSV path")
    args = parser.parse_args()

    env = MarsEnvironment()
    all_results: list[EpisodeResult] = []

    for name in args.agents:
        print(f"\nRunning {args.episodes} episodes with '{name}'...")
        agent_results: list[EpisodeResult] = []
        for i in range(args.episodes):
            seed = args.seed + i
            agent = make_agent(name, seed)
            r = run_episode(agent, env, seed)
            agent_results.append(r)
        all_results.extend(agent_results)
        summary = summarize(agent_results)
        print(f"  success_rate : {summary.success_rate:.1%}")
        print(f"  avg_samples  : {summary.avg_samples:.2f}")
        print(f"  avg_steps    : {summary.avg_steps:.1f}")
        print(f"  top_failure  : {summary.top_failure}")

    # Save results
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(all_results[0]).keys()))
        writer.writeheader()
        for r in all_results:
            writer.writerow(asdict(r))
    print(f"\nSaved {len(all_results)} rows to {out_path}")

    # Print comparison table
    print("\n=== COMPARISON ===")
    print(f"{'agent':<12} {'success':>8} {'samples':>8} {'steps':>8} {'energy':>8}")
    print("-" * 50)
    for name in args.agents:
        rows = [r for r in all_results if r.agent == name]
        s = summarize(rows)
        print(f"{s.agent:<12} {s.success_rate:>7.1%} "
              f"{s.avg_samples:>8.2f} {s.avg_steps:>8.1f} "
              f"{s.avg_energy_left:>8.1f}")


if __name__ == "__main__":
    main()