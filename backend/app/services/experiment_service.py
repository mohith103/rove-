"""Run batches of missions and aggregate results."""
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

from agents.commander import Commander
from agents.planner import Planner
from agents.random_agent import RandomAgent
from agents.rule_based import RuleBasedAgent
from simulation.config import load_config_for_difficulty
from simulation.environment import MarsEnvironment


@dataclass
class EpisodeResult:
    success: bool
    samples: int
    steps: int
    energy_left: float
    oxygen_left: float
    reward: float
    failure_reason: str | None


def _build_policy(agent_name: str, seed: int):
    if agent_name == "random":
        return RandomAgent(seed=seed)
    if agent_name == "rule_based":
        return RuleBasedAgent()
    if agent_name == "ppo":
        try:
            from backend.app.services.mission_service import _PPOWrapper
            return _PPOWrapper("reinforcement_learning/models/best/best_model.zip")
        except FileNotFoundError:
            raise RuntimeError(
                "PPO model not found. Train one or use rule_based/random."
            )
    raise ValueError(f"unknown agent: {agent_name}")


def run_one_episode(
    agent_name: str,
    difficulty: str,
    mode: str,
    seed: int,
    max_steps: int | None,
) -> EpisodeResult:
    cfg = load_config_for_difficulty(difficulty)
    if max_steps is not None:
        cfg.mission.max_steps = max_steps

    env = MarsEnvironment(cfg)
    state = env.reset(seed=seed)

    policy = _build_policy(agent_name, seed)
    commander = Commander(policy=policy, planner=Planner(mode=mode))

    total_reward = 0.0
    done = False
    while not done:
        decision = commander.decide(state)
        state, reward, done, _info = env.step(decision.action)
        total_reward += reward

    return EpisodeResult(
        success=state.success,
        samples=state.rover.samples_collected,
        steps=state.step,
        energy_left=state.rover.energy,
        oxygen_left=state.rover.oxygen,
        reward=total_reward,
        failure_reason=state.failure_reason,
    )


def run_batch(
    agents: list[str],
    difficulties: list[str],
    mode: str,
    episodes: int,
    seed: int,
    max_steps: int | None,
) -> tuple[list[dict], int, float]:
    start = time.time()
    rows: list[dict] = []
    total = 0

    for agent_name in agents:
        for difficulty in difficulties:
            results: list[EpisodeResult] = []
            for i in range(episodes):
                ep_seed = seed + i
                result = run_one_episode(
                    agent_name=agent_name,
                    difficulty=difficulty,
                    mode=mode,
                    seed=ep_seed,
                    max_steps=max_steps,
                )
                results.append(result)
                total += 1

            n = len(results)
            reasons = [r.failure_reason for r in results if r.failure_reason]
            top_failure = statistics.mode(reasons) if reasons else "none"

            rows.append({
                "agent": agent_name,
                "difficulty": difficulty,
                "episodes": n,
                "success_rate": sum(1 for r in results if r.success) / n,
                "avg_samples": sum(r.samples for r in results) / n,
                "avg_steps": sum(r.steps for r in results) / n,
                "avg_energy_left": sum(r.energy_left for r in results) / n,
                "avg_oxygen_left": sum(r.oxygen_left for r in results) / n,
                "avg_reward": sum(r.reward for r in results) / n,
                "top_failure": top_failure,
            })

    elapsed = time.time() - start
    return rows, total, elapsed
