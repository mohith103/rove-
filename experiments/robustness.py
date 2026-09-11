"""Run every agent on every difficulty and produce a comparison matrix.

Usage:
    python -m experiments.robustness --episodes 30
    python -m experiments.robustness --episodes 50 --model reinforcement_learning/models/best/best_model.zip
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from agents.random_agent import RandomAgent
from agents.rule_based import RuleBasedAgent
from reinforcement_learning.env import RoveEnv
from simulation.config import load_config_for_difficulty
from simulation.environment import MarsEnvironment


DIFFICULTIES = ["easy", "medium", "hard", "extreme"]


@dataclass
class Row:
    difficulty: str
    agent: str
    episodes: int
    success_rate: float
    avg_samples: float
    avg_steps: float
    avg_energy_left: float


def run_scripted(agent, difficulty: str, episodes: int, seed: int) -> Row:
    cfg = load_config_for_difficulty(difficulty)
    env = MarsEnvironment(cfg)
    successes, samples, steps, energies = [], [], [], []
    for i in range(episodes):
        agent.reset()
        state = env.reset(seed=seed + i)
        done = False
        while not done:
            action = agent.act(state)
            state, _, done, _ = env.step(action)
        successes.append(1 if state.success else 0)
        samples.append(state.rover.samples_collected)
        steps.append(state.step)
        energies.append(state.rover.energy)
    return Row(
        difficulty=difficulty,
        agent=agent.name,
        episodes=episodes,
        success_rate=sum(successes) / episodes,
        avg_samples=float(np.mean(samples)),
        avg_steps=float(np.mean(steps)),
        avg_energy_left=float(np.mean(energies)),
    )


def run_ppo(model, difficulty: str, episodes: int, seed: int) -> Row:
    cfg = load_config_for_difficulty(difficulty)
    env = RoveEnv(config=cfg)
    successes, samples, steps, energies = [], [], [], []
    for i in range(episodes):
        obs, _ = env.reset(seed=seed + i)
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, term, trunc, _ = env.step(int(action))
            done = term or trunc
        state = env.sim.get_state()
        successes.append(1 if state.success else 0)
        samples.append(state.rover.samples_collected)
        steps.append(state.step)
        energies.append(state.rover.energy)
    return Row(
        difficulty=difficulty,
        agent="ppo",
        episodes=episodes,
        success_rate=sum(successes) / episodes,
        avg_samples=float(np.mean(samples)),
        avg_steps=float(np.mean(steps)),
        avg_energy_left=float(np.mean(energies)),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=5000)
    parser.add_argument("--model", type=str,
                        default="reinforcement_learning/models/best/best_model.zip")
    parser.add_argument("--out", type=str,
                        default="experiments/results/robustness.csv")
    args = parser.parse_args()

    model = None
    if Path(args.model).exists():
        model = PPO.load(args.model)
        print(f"Loaded PPO model from {args.model}")
    else:
        print(f"PPO model not found at {args.model}; skipping PPO rows.")

    rows: list[Row] = []
    for diff in DIFFICULTIES:
        print(f"\n=== Difficulty: {diff} ===")
        print(f"  random ...")
        rows.append(run_scripted(RandomAgent(seed=0), diff, args.episodes, args.seed))
        print(f"  rule_based ...")
        rows.append(run_scripted(RuleBasedAgent(), diff, args.episodes, args.seed))
        if model is not None:
            print(f"  ppo ...")
            rows.append(run_ppo(model, diff, args.episodes, args.seed))

    # Save CSV
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))

    # Print matrix
    print("\n=== ROBUSTNESS MATRIX (success rate) ===")
    header = f"{'agent':<12}" + "".join(f"{d:>10}" for d in DIFFICULTIES)
    print(header)
    print("-" * len(header))
    agents = sorted({r.agent for r in rows})
    for a in agents:
        cells = []
        for d in DIFFICULTIES:
            row = next((r for r in rows if r.agent == a and r.difficulty == d), None)
            cells.append(f"{row.success_rate:>9.1%}" if row else f"{'—':>10}")
        print(f"{a:<12}" + "".join(cells))

    print(f"\nSaved {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()