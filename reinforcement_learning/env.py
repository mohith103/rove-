"""Gymnasium wrapper for the ROVE Mars simulation."""
from __future__ import annotations

from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from simulation.config import RoveConfig, load_config
from simulation.environment import Action, MarsEnvironment
from simulation.state import MissionState
from simulation.terrain import TerrainType
from simulation.events import EventType
from simulation.weather import WeatherType

# Number of terrain types (matches TerrainType enum)
N_TERRAIN = 7

# Layout of the observation vector (documentation as code)
OBS_LAYOUT = [
    "rover_x", "rover_y",
    "base_x", "base_y",
    "distance_to_base",
    "distance_to_nearest_site",
    "energy", "water", "oxygen", "food",
    "battery_health", "rover_health",
    "communication", "temperature",
    "samples_progress", "steps_remaining_fraction",
    "cargo_fraction",
    # + N_TERRAIN terrain one-hot (under rover)
    # + N_TERRAIN * 4 neighbors (N, S, E, W)
]


def _obs_dim(config: RoveConfig) -> int:
    """Observation vector length.

    Breakdown:
        17 scalar features
        7  terrain one-hot (under rover)
        28 terrain one-hot (4 neighbors × 7)
        5  weather one-hot
        8  active failure flags (7 events + spare)
        1  weather remaining fraction
        ---
        66
    """
    return 17 + 7 + (7 * 4) + 5 + 8 + 1


class RoveEnv(gym.Env):
    """Gymnasium environment for ROVE.

    Observation: float32 vector of length `_obs_dim(cfg)`.
    Action: Discrete(11) — matches simulation.environment.Action.
    """

    metadata = {"render_modes": ["ansi"], "render_fps": 4}

    def __init__(
        self,
        config: RoveConfig | None = None,
        render_mode: str | None = None,
        max_steps: int | None = None,
    ) -> None:
        super().__init__()
        self.cfg = config or load_config()
        self.render_mode = render_mode

        # Allow overriding the mission length for training
        if max_steps is not None:
            self.cfg.mission.max_steps = max_steps

        self.sim = MarsEnvironment(self.cfg)

        obs_dim = _obs_dim(self.cfg)
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(obs_dim,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(Action.N_ACTIONS)

        self._state: MissionState | None = None
        self._prev_distance_to_site: float | None = None

    # ---------- Gymnasium API ----------

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        self._state = self.sim.reset(seed=seed)
        self._prev_distance_to_site = self._distance_to_nearest_site(self._state)
        obs = self._observe(self._state)
        info = {"step": 0}
        return obs, info

    def step(
        self, action: int
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        assert self._state is not None, "call reset() before step()"

        # Environment-level reward shaping: reward progress toward site
        prev_dist = self._prev_distance_to_site

        state, sim_reward, done, info = self.sim.step(int(action))

        new_dist = self._distance_to_nearest_site(state)
        shaping = 0.0
        if prev_dist is not None and new_dist is not None:
            shaping = 0.05 * (prev_dist - new_dist)  # positive if we got closer

        self._prev_distance_to_site = new_dist
        self._state = state

        # Split done into terminated/truncated per Gymnasium 0.26+ API
        terminated = done and state.failure_reason != "Time limit reached"
        truncated = done and state.failure_reason == "Time limit reached"

        reward = float(sim_reward + shaping)
        obs = self._observe(state)
        info.update({"step": state.step, "sim_reward": sim_reward, "shaping": shaping})

        return obs, reward, terminated, truncated, info

    def render(self) -> str | None:
        """Return an ASCII grid of the current world."""
        if self._state is None:
            return None
        env = self.sim
        assert env.terrain is not None and env.rover is not None
        glyphs = {
            TerrainType.PLAIN: ".",
            TerrainType.ROCK: "R",
            TerrainType.CRATER: "O",
            TerrainType.MOUNTAIN: "^",
            TerrainType.SAND: "s",
            TerrainType.BASE: "H",
            TerrainType.SCIENCE_SITE: "*",
        }
        rows: list[str] = []
        for y in range(env.terrain.height):
            row: list[str] = []
            for x in range(env.terrain.width):
                if (x, y) == (env.rover.x, env.rover.y):
                    row.append("X")
                elif (x, y) == (env.base.x, env.base.y):
                    row.append("H")
                else:
                    row.append(glyphs[env.terrain.get(x, y)])
            rows.append(" ".join(row))
        text = "\n".join(rows)
        if self.render_mode == "ansi":
            return text
        print(text)
        return text

    # ---------- Observation builder ----------

    def _observe(self, state: MissionState) -> np.ndarray:
        """Build the normalized observation vector."""
        rover = state.rover
        base = state.base
        terrain = state.terrain

        d_base = self._manhattan(rover.x, rover.y, base.x, base.y)
        d_site = self._distance_to_nearest_site(state)
        d_site = float(d_site) if d_site is not None else 0.0

        samples_progress = (
            rover.samples_collected / max(1, self.cfg.mission.success_samples_required)
        )
        steps_remaining = (state.max_steps - state.step) / max(1, state.max_steps)
        cargo_fraction = len(rover.cargo) / max(1, rover.cargo_capacity)

        norm_w = max(1, terrain.width - 1)
        norm_h = max(1, terrain.height - 1)

        scalars = np.array([
            (rover.x / norm_w) * 2 - 1,
            (rover.y / norm_h) * 2 - 1,
            (base.x / norm_w) * 2 - 1,
            (base.y / norm_h) * 2 - 1,
            d_base / (terrain.width + terrain.height),
            d_site / (terrain.width + terrain.height),
            rover.energy / 100.0,
            rover.water / 100.0,
            rover.oxygen / 100.0,
            rover.food / 100.0,
            rover.battery_health / 100.0,
            rover.rover_health / 100.0,
            rover.communication / 100.0,
            rover.temperature / 100.0,
            min(1.0, samples_progress),
            max(0.0, min(1.0, steps_remaining)),
            cargo_fraction,
        ], dtype=np.float32)

        # Terrain under rover + 4 neighbors
        terrain_features = np.zeros(N_TERRAIN * 5, dtype=np.float32)
        terrain_features[:N_TERRAIN] = self._onehot(terrain.get(rover.x, rover.y))
        neighbors = [
            (rover.x, rover.y - 1),
            (rover.x, rover.y + 1),
            (rover.x + 1, rover.y),
            (rover.x - 1, rover.y),
        ]
        for i, (nx, ny) in enumerate(neighbors):
            start = N_TERRAIN * (i + 1)
            terrain_features[start:start + N_TERRAIN] = self._onehot(
                terrain.get(nx, ny)
            )

        # Weather one-hot (5 types)
        weather_vec = np.zeros(5, dtype=np.float32)
        weather_remaining = 0.0
        if self.sim.weather is not None:
            weather_vec[int(self.sim.weather.current)] = 1.0
            weather_remaining = min(1.0, self.sim.weather.remaining_steps / 30.0)

        # Failure flags (8 slots)
        failure_vec = np.zeros(8, dtype=np.float32)
        if self.sim.events is not None:
            for f in self.sim.events.active:
                idx = int(f.type)
                if 0 <= idx < 8:
                    failure_vec[idx] = f.severity

        extra = np.concatenate([
            weather_vec,
            failure_vec,
            np.array([weather_remaining], dtype=np.float32),
        ])

        obs = np.concatenate([scalars, terrain_features, extra]).astype(np.float32)
        assert obs.shape == self.observation_space.shape, (
            f"obs shape {obs.shape} != {self.observation_space.shape}"
        )
        return np.clip(obs, -1.0, 1.0)

    # ---------- Helpers ----------

    @staticmethod
    def _manhattan(x1: int, y1: int, x2: int, y2: int) -> int:
        return abs(x1 - x2) + abs(y1 - y2)

    def _distance_to_nearest_site(self, state: MissionState) -> float | None:
        remaining = [s for s in state.science_sites if not s.collected]
        if not remaining:
            return None
        rx, ry = state.rover.x, state.rover.y
        return float(min(abs(s.x - rx) + abs(s.y - ry) for s in remaining))

    @staticmethod
    def _onehot(t: TerrainType) -> np.ndarray:
        v = np.zeros(N_TERRAIN, dtype=np.float32)
        v[int(t)] = 1.0
        return v