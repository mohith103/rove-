"""In-memory mission registry with per-step state history."""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents.base_agent import BaseAgent
from agents.commander import Commander
from agents.planner import Planner
from agents.random_agent import RandomAgent
from agents.rule_based import RuleBasedAgent
from agents.specialists.commander import MultiAgentCommander
from simulation.config import load_config_for_difficulty
from simulation.environment import MarsEnvironment
from simulation.state import MissionState


MAX_FRAMES = 2000


@dataclass
class Mission:
    id: str
    difficulty: str
    agent_name: str
    mode: str
    seed: int
    env: MarsEnvironment
    policy: BaseAgent
    commander: Any
    multi_agent: bool = False
    status: str = "running"
    state: MissionState | None = None
    decisions: list[dict[str, Any]] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    frames: list[dict[str, Any]] = field(default_factory=list)
    frame_decisions: list[dict[str, Any] | None] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def step_once(self) -> None:
        with self.lock:
            if self.status != "running" or self.state is None or self.state.done:
                return
            decision = self.commander.decide(self.state)
            decision_dict = decision.to_dict()
            self.decisions.append(decision_dict)
            action = decision.action
            state, _reward, done, info = self.env.step(action)
            self.state = state
            self.events = list(state.events_log)
            self._record_frame(state, decision_dict)
            if done:
                self.status = "done"

    def _record_frame(self, state: MissionState, decision: dict[str, Any] | None) -> None:
        snapshot = {
            "step": state.step,
            "rover": state.rover.to_dict(),
            "base": state.base.to_dict(),
            "science_sites": [s.to_dict() for s in state.science_sites],
            "done": state.done,
            "success": state.success,
            "failure_reason": state.failure_reason,
        }
        self.frames.append(snapshot)
        self.frame_decisions.append(decision)
        if len(self.frames) > MAX_FRAMES:
            self.frames = self.frames[-MAX_FRAMES:]
            self.frame_decisions = self.frame_decisions[-MAX_FRAMES:]

    def to_summary(self) -> dict[str, Any]:
        s = self.state
        return {
            "id": self.id,
            "difficulty": self.difficulty,
            "agent": self.agent_name,
            "mode": self.mode,
            "seed": self.seed,
            "status": self.status,
            "step": s.step if s else 0,
            "max_steps": s.max_steps if s else 0,
            "success": s.success if s else False,
            "failure_reason": s.failure_reason if s else None,
            "multi_agent": self.multi_agent,
        }

    def world_state(self, event_limit: int = 100) -> dict[str, Any]:
        s = self.state
        if s is None:
            return {}
        return {
            "step": s.step,
            "max_steps": s.max_steps,
            "rover": s.rover.to_dict(),
            "base": s.base.to_dict(),
            "science_sites": [site.to_dict() for site in s.science_sites],
            "done": s.done,
            "success": s.success,
            "failure_reason": s.failure_reason,
            "events": list(s.events_log[-event_limit:]),
            "terrain": s.terrain.to_list(),
            "width": s.terrain.width,
            "height": s.terrain.height,
        }

    def to_detail(self) -> dict[str, Any]:
        last_decision = self.decisions[-1] if self.decisions else None
        return {
            "id": self.id,
            "difficulty": self.difficulty,
            "agent": self.agent_name,
            "mode": self.mode,
            "seed": self.seed,
            "status": self.status,
            "state": self.world_state(event_limit=10_000),
            "decision": last_decision,
            "events": self.events,
            "multi_agent": self.multi_agent,
        }

    def to_replay(self) -> dict[str, Any]:
        s = self.state
        if s is None:
            return {}
        return {
            "id": self.id,
            "difficulty": self.difficulty,
            "agent": self.agent_name,
            "mode": self.mode,
            "seed": self.seed,
            "status": self.status,
            "success": s.success,
            "failure_reason": s.failure_reason,
            "max_steps": s.max_steps,
            "width": s.terrain.width,
            "height": s.terrain.height,
            "terrain": s.terrain.to_list(),
            "frames": self.frames,
            "decisions": self.frame_decisions,
            "events": self.events,
            "multi_agent": self.multi_agent,
        }


class MissionService:
    def __init__(self, model_dir: str = "reinforcement_learning/models") -> None:
        self._missions: dict[str, Mission] = {}
        self._lock = threading.Lock()
        self.model_dir = Path(model_dir)

    def create_mission(
        self,
        difficulty: str,
        agent_name: str,
        mode: str,
        seed: int,
        model_path: str | None = None,
        max_steps: int | None = None,
        multi_agent: bool = False,
    ) -> Mission:
        cfg = load_config_for_difficulty(difficulty)
        if max_steps is not None:
            cfg.mission.max_steps = max_steps
        env = MarsEnvironment(cfg)
        state = env.reset(seed=seed)

        env.rover.x = env.base.x
        env.rover.y = env.base.y
        state = env.get_state()

        policy = self._build_policy(agent_name, seed, model_path)

        if multi_agent:
            commander: Any = MultiAgentCommander(mode=mode)
        else:
            commander = Commander(policy=policy, planner=Planner(mode=mode))

        mission = Mission(
            id=str(uuid.uuid4())[:8],
            difficulty=difficulty,
            agent_name=agent_name,
            mode=mode,
            seed=seed,
            env=env,
            policy=policy,
            commander=commander,
            multi_agent=multi_agent,
            state=state,
            events=list(state.events_log),
        )

        mission._record_frame(state, None)

        with self._lock:
            self._missions[mission.id] = mission
        return mission

    def get(self, mission_id: str) -> Mission | None:
        with self._lock:
            return self._missions.get(mission_id)

    def list_all(self) -> list[Mission]:
        with self._lock:
            return list(self._missions.values())

    def pause(self, mission_id: str) -> bool:
        m = self.get(mission_id)
        if m is None:
            return False
        with m.lock:
            if m.status == "running":
                m.status = "paused"
                return True
        return False

    def resume(self, mission_id: str) -> bool:
        m = self.get(mission_id)
        if m is None:
            return False
        with m.lock:
            if m.status == "paused":
                m.status = "running"
                return True
        return False

    def step_manual(self, mission_id: str, action: int) -> bool:
        m = self.get(mission_id)
        if m is None or m.state is None:
            return False
        with m.lock:
            state, _r, done, _info = m.env.step(action)
            m.state = state
            m.events = list(state.events_log)
            m._record_frame(state, None)
            if done:
                m.status = "done"
        return True

    def _build_policy(self, agent_name: str, seed: int, model_path: str | None) -> BaseAgent:
        if agent_name == "random":
            return RandomAgent(seed=seed)
        if agent_name == "rule_based":
            return RuleBasedAgent()
        if agent_name == "ppo":
            return _PPOWrapper(model_path or self._default_model_path())
        raise ValueError(f"unknown agent: {agent_name}")

    def _default_model_path(self) -> str:
        best = self.model_dir / "best" / "best_model.zip"
        if best.exists():
            return str(best)
        return str(self.model_dir / "ppo_rove.zip")


class _PPOWrapper(BaseAgent):
    name = "ppo"

    def __init__(self, model_path: str) -> None:
        from stable_baselines3 import PPO
        from reinforcement_learning.env import RoveEnv

        if not Path(model_path).exists():
            raise FileNotFoundError(f"PPO model not found: {model_path}")

        self.model = PPO.load(model_path)
        self._env = RoveEnv()

    def act(self, state: MissionState) -> int:
        self._env.sim.rover = state.rover
        self._env.sim.base = state.base
        self._env.sim.terrain = state.terrain
        self._env.sim.science_sites = state.science_sites
        self._env._state = state
        obs = self._env._observe(state)
        action, _ = self.model.predict(obs, deterministic=True)
        return int(action)
