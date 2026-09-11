"""Counterfactual simulation service.

Runs a fork from a specific step in a completed mission and compares the
result to the original.

Mechanics:
    - Environment is deterministic given (config, seed).
    - We replay the original decisions up to the fork step to reconstruct
      the exact state at that point.
    - Then we apply an override policy for N steps, then resume the
      original policy.
    - We capture frames for both timelines and return them.
"""
from __future__ import annotations

from typing import Any

from agents.commander import Commander
from agents.planner import Planner
from agents.random_agent import RandomAgent
from agents.rule_based import RuleBasedAgent
from backend.app.services.mission_service import Mission
from simulation.config import load_config_for_difficulty
from simulation.environment import Action, MarsEnvironment


# Map override names to their Action IDs
_OVERRIDE_ACTIONS = {
    "force_return_to_base": Action.RETURN_TO_BASE,
    "force_recharge": Action.RECHARGE,
    "force_repair": Action.REPAIR,
    "force_wait": Action.WAIT,
}


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
            raise RuntimeError("PPO model not found.")
    raise ValueError(f"unknown agent: {agent_name}")


def _snapshot_frame(state) -> dict[str, Any]:
    return {
        "step": state.step,
        "rover": state.rover.to_dict(),
        "base": state.base.to_dict(),
        "science_sites": [s.to_dict() for s in state.science_sites],
        "done": state.done,
        "success": state.success,
        "failure_reason": state.failure_reason,
    }


def _run_timeline(
    original: Mission,
    fork_step: int,
    override_action: int | None,
    override_duration: int,
) -> dict[str, Any]:
    """Replay the mission, forking at `fork_step`.

    Returns a CounterfactualTimeline-shaped dict.
    """
    cfg = load_config_for_difficulty(original.difficulty)
    if original.state is not None:
        cfg.mission.max_steps = original.state.max_steps

    env = MarsEnvironment(cfg)
    state = env.reset(seed=original.seed)
    # Lock rover to base to match mission_service
    env.rover.x = env.base.x
    env.rover.y = env.base.y
    state = env.get_state()

    policy = _build_policy(original.agent_name, original.seed)
    commander = Commander(policy=policy, planner=Planner(mode=original.mode))

    frames: list[dict[str, Any]] = [_snapshot_frame(state)]

    # Replay up to fork_step - 1 (the state we want to fork from)
    target_index = min(fork_step, len(original.decisions))
    step = 0
    done = False

    # Phase 1: replay original decisions up to the fork point
    while step < target_index and not done:
        decision = original.decisions[step]
        action = decision["action"]
        state, _reward, done, _info = env.step(action)
        step += 1
        frames.append(_snapshot_frame(state))

    # Phase 2: apply override for N steps
    override_steps_applied = 0
    while (
        override_action is not None
        and override_steps_applied < override_duration
        and not done
    ):
        state, _reward, done, _info = env.step(override_action)
        step += 1
        override_steps_applied += 1
        frames.append(_snapshot_frame(state))

    # Phase 3: resume the policy
    while not done:
        decision = commander.decide(state)
        state, _reward, done, _info = env.step(decision.action)
        step += 1
        frames.append(_snapshot_frame(state))

    final = frames[-1]
    return {
        "label": "",
        "description": "",
        "success": final["success"],
        "steps": final["step"],
        "samples_collected": final["rover"]["samples_collected"],
        "energy_left": final["rover"]["energy"],
        "oxygen_left": final["rover"]["oxygen"],
        "rover_health": final["rover"]["rover_health"],
        "failure_reason": final["failure_reason"],
        "frames": frames,
    }


def run_counterfactual(
    mission: Mission,
    fork_step: int,
    override: str,
    override_duration: int,
    custom_action: int | None,
) -> dict[str, Any]:
    """Run the counterfactual and build the comparison response."""

    # Resolve the override action
    if override == "custom_action":
        if custom_action is None:
            raise ValueError("custom_action must be provided when override='custom_action'")
        override_action = custom_action
    else:
        override_action = _OVERRIDE_ACTIONS.get(override)
        if override_action is None:
            raise ValueError(f"unknown override: {override}")

    # --- Run counterfactual ---
    cf_timeline = _run_timeline(
        original=mission,
        fork_step=fork_step,
        override_action=override_action,
        override_duration=override_duration,
    )
    cf_timeline["label"] = "counterfactual"
    cf_timeline["description"] = (
        f"Applying '{override}' for {override_duration} steps "
        f"starting at SOL {fork_step}."
    )

    # --- Rebuild actual timeline from stored frames ---
    actual_frames = mission.frames
    if not actual_frames:
        raise ValueError("mission has no stored frames to compare against")

    last_actual = actual_frames[-1]
    actual_timeline = {
        "label": "actual",
        "description": "The mission as originally run.",
        "success": last_actual["success"],
        "steps": last_actual["step"],
        "samples_collected": last_actual["rover"]["samples_collected"],
        "energy_left": last_actual["rover"]["energy"],
        "oxygen_left": last_actual["rover"]["oxygen"],
        "rover_health": last_actual["rover"]["rover_health"],
        "failure_reason": last_actual["failure_reason"],
        "frames": actual_frames,
    }

    # --- Verdict ---
    verdict = _build_verdict(actual_timeline, cf_timeline)

    return {
        "mission_id": mission.id,
        "fork_step": fork_step,
        "override": override,
        "override_duration": override_duration,
        "actual": actual_timeline,
        "counterfactual": cf_timeline,
        "verdict": verdict,
    }


def _build_verdict(actual: dict[str, Any], cf: dict[str, Any]) -> str:
    """Short human-readable verdict comparing the two timelines."""
    a_ok = actual["success"]
    c_ok = cf["success"]

    if not a_ok and c_ok:
        return "Counterfactual succeeded where the actual mission failed."
    if a_ok and not c_ok:
        return "Counterfactual failed where the actual mission succeeded."
    if a_ok and c_ok:
        a_samples = actual["samples_collected"]
        c_samples = cf["samples_collected"]
        if c_samples > a_samples:
            return (
                f"Both succeeded; counterfactual collected "
                f"{c_samples - a_samples} more sample(s)."
            )
        if c_samples < a_samples:
            return (
                f"Both succeeded; counterfactual collected "
                f"{a_samples - c_samples} fewer sample(s)."
            )
        return "Both succeeded with the same number of samples."
    # both failed
    return (
        f"Both failed. Actual: '{actual['failure_reason']}'. "
        f"Counterfactual: '{cf['failure_reason']}'."
    )