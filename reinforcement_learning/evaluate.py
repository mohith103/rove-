"""Evaluate a trained PPO model against baselines on identical missions.

Usage:
    python -m reinforcement_learning.evaluate --model reinforcement_learning/models/ppo_rove.zip
    python -m reinforcement_learning.evaluate --episodes 30
    python -m reinforcement_learning.evaluate --episodes 30 --difficulty hard
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from agents.random_agent import RandomAgent
from agents.rule_based import RuleBasedAgent
from reinforcement_learning.env import RoveEnv
from simulation.config import load_config_for_difficulty
from simulation.environment import MarsEnvironment


@dataclass
class EvalResult:
    agent: str
    episodes: int
    success_rate: float
    avg_samples: float
    avg_steps: float
    avg_energy_left: float
    avg_reward: float


def eval_ppo(model_path: str, episodes: int, seed: int, cfg) -> EvalResult:
    model = PPO.load(model_path)
    env = RoveEnv(config=cfg)
    rewards: list[float] = []
    samples: list[int] = []
    steps: list[int] = []
    successes: list[int] = []
    energies: list[float] = []

    for i in range(episodes):
        obs, _ = env.reset(seed=seed + i)
        done = False
        ep_r = 0.0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, r, term, trunc, _ = env.step(int(action))
            ep_r += r
            done = term or trunc
        state = env.sim.get_state()
        rewards.append(ep_r)
        samples.append(state.rover.samples_collected)
        steps.append(state.step)
        successes.append(1 if state.success else 0)
        energies.append(state.rover.energy)

    return EvalResult(
        agent="ppo",
        episodes=episodes,
        success_rate=sum(successes) / episodes,
        avg_samples=float(np.mean(samples)),
        avg_steps=float(np.mean(steps)),
        avg_energy_left=float(np.mean(energies)),
        avg_reward=float(np.mean(rewards)),
    )


def eval_scripted(agent, episodes: int, seed: int, name: str, cfg) -> EvalResult:
    env = MarsEnvironment(config=cfg)
    rewards: list[float] = []
    samples: list[int] = []
    steps: list[int] = []
    successes: list[int] = []
    energies: list[float] = []

    for i in range(episodes):
        agent.reset()
        state = env.reset(seed=seed + i)
        ep_r = 0.0
        done = False
        while not done:
            action = agent.act(state)
            state, r, done, _ = env.step(action)
            ep_r += r
        rewards.append(ep_r)
        samples.append(state.rover.samples_collected)
        steps.append(state.step)
        successes.append(1 if state.success else 0)
        energies.append(state.rover.energy)

    return EvalResult(
        agent=name,
        episodes=episodes,
        success_rate=sum(successes) / episodes,
        avg_samples=float(np.mean(samples)),
        avg_steps=float(np.mean(steps)),
        avg_energy_left=float(np.mean(energies)),
        avg_reward=float(np.mean(rewards)),
    )


def print_table(results: list[EvalResult]) -> None:
    print()
    print(f"{'agent':<12} {'success':>9} {'samples':>9} "
          f"{'steps':>9} {'energy':>9} {'reward':>10}")
    print("-" * 62)
    for r in results:
        print(f"{r.agent:<12} {r.success_rate:>8.1%} "
              f"{r.avg_samples:>9.2f} {r.avg_steps:>9.1f} "
              f"{r.avg_energy_left:>9.1f} {r.avg_reward:>10.1f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str,
                        default="reinforcement_learning/models/ppo_rove.zip")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--difficulty", type=str, default="default",
                        choices=["easy", "medium", "hard", "extreme", "default"],
                        help="which difficulty preset to evaluate on")
    args = parser.parse_args()

    cfg = load_config_for_difficulty(args.difficulty)

    print(f"Evaluating {args.episodes} missions per agent...")
    print(f"  difficulty: {args.difficulty}")
    print(f"  seed base : {args.seed}")
    print(f"  model     : {args.model}")

    results: list[EvalResult] = []

    print("\n[1/3] Random agent...")
    results.append(eval_scripted(RandomAgent(seed=0), args.episodes,
                                 args.seed, "random", cfg))

    print("[2/3] Rule-based agent...")
    results.append(eval_scripted(RuleBasedAgent(), args.episodes,
                                 args.seed, "rule_based", cfg))

    print("[3/3] PPO agent...")
    if Path(args.model).exists():
        results.append(eval_ppo(args.model, args.episodes, args.seed, cfg))
    else:
        print(f"  WARNING: model {args.model} not found. Skipping PPO.")

    print_table(results)


if __name__ == "__main__":
    main()