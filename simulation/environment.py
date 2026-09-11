"""ROVE Mars simulation environment."""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

from simulation.base import BaseStation
from simulation.config import RoveConfig, load_config
from simulation.events import EventEngine, EventType
from simulation.rover import Rover
from simulation.state import MissionState, ScienceSite
from simulation.terrain import TERRAIN_NAMES, Terrain, TerrainType
from simulation.weather import Weather

logger = logging.getLogger(__name__)


class Action:
    """Discrete action space for the ROVE rover."""
    MOVE_NORTH = 0
    MOVE_SOUTH = 1
    MOVE_EAST = 2
    MOVE_WEST = 3
    COLLECT_SAMPLE = 4
    ANALYZE_SAMPLE = 5
    RETURN_TO_BASE = 6
    RECHARGE = 7
    REPAIR = 8
    COMMUNICATE = 9
    WAIT = 10

    NAMES = {
        0: "MOVE_NORTH", 1: "MOVE_SOUTH", 2: "MOVE_EAST", 3: "MOVE_WEST",
        4: "COLLECT_SAMPLE", 5: "ANALYZE_SAMPLE", 6: "RETURN_TO_BASE",
        7: "RECHARGE", 8: "REPAIR", 9: "COMMUNICATE", 10: "WAIT",
    }
    N_ACTIONS = 11


class MarsEnvironment:
    """The core ROVE simulation."""

    def __init__(self, config: RoveConfig | None = None) -> None:
        self.cfg = config or load_config()
        self.terrain: Terrain | None = None
        self.rover: Rover | None = None
        self.base: BaseStation | None = None
        self.science_sites: list[ScienceSite] = []
        self.step_count = 0
        self.done = False
        self.success = False
        self.failure_reason: str | None = None
        self.event_log: list[str] = []
        self.events: EventEngine | None = None
        self.weather: Weather | None = None
        self.rng: np.random.Generator | None = None

    # ---------- Lifecycle ----------

    def reset(self, seed: int | None = None) -> MissionState:
        """Reset the environment. Same seed produces the same world."""
        if seed is None:
            seed = self.cfg.map.seed
        self.rng = np.random.default_rng(seed)

        # 1. Terrain
        self.terrain = Terrain(self.cfg.map.width, self.cfg.map.height, seed=seed)
        self.terrain.generate(self.cfg.terrain.model_dump())

        # 2. Base — always at (cfg.base.x, cfg.base.y)
        self.base = BaseStation(
            x=self.cfg.base.x,
            y=self.cfg.base.y,
            recharge_rate=self.cfg.base.recharge_rate,
        )
        self.terrain.set(self.base.x, self.base.y, TerrainType.BASE)

        # 3. Rover — ALWAYS starts on the base station.
        self.rover = Rover.from_config(self.cfg.rover)
        self.rover.x = self.base.x
        self.rover.y = self.base.y

        # 4. Science sites — placed anywhere passable except base cell
        self.science_sites = self._generate_science_sites()
        for s in self.science_sites:
            self.terrain.set(s.x, s.y, TerrainType.SCIENCE_SITE)

        # 5. Weather + events engines
        self.weather = Weather(
            weather_cfg=self.cfg.weather.model_dump(),
            rng=np.random.default_rng(seed + 1),
        )
        self.events = EventEngine(
            config=self.cfg.events.model_dump(),
            rng=np.random.default_rng(seed + 2),
        )

        # 6. Counters
        self.step_count = 0
        self.done = False
        self.success = False
        self.failure_reason = None
        self.event_log = []
        self._log_event("Mission started at base.")

        return self.get_state()

    def _generate_science_sites(self) -> list[ScienceSite]:
        """Place N science sites at random free, passable cells."""
        assert self.terrain and self.base and self.rover
        sites: list[ScienceSite] = []
        occupied = {(self.base.x, self.base.y), (self.rover.x, self.rover.y)}
        sample_types = ["basalt", "hematite", "olivine", "sulfate", "clay"]

        attempts = 0
        while len(sites) < self.cfg.science.num_sites and attempts < 1000:
            attempts += 1
            x = int(self.rng.integers(0, self.terrain.width))
            y = int(self.rng.integers(0, self.terrain.height))
            if (x, y) in occupied or not self.terrain.is_passable(x, y):
                continue
            occupied.add((x, y))
            sites.append(ScienceSite(
                x=x, y=y,
                value=int(self.rng.integers(self.cfg.science.min_value,
                                            self.cfg.science.max_value + 1)),
                difficulty=int(self.rng.integers(self.cfg.science.min_difficulty,
                                                 self.cfg.science.max_difficulty + 1)),
                sample_type=str(self.rng.choice(sample_types)),
            ))
        return sites

    # ---------- Core loop ----------

    def step(self, action: int) -> tuple[MissionState, float, bool, dict[str, Any]]:
        """Apply one action. Returns (state, reward, done, info)."""
        assert self.rover and self.terrain and self.base
        if self.done:
            return self.get_state(), 0.0, True, {"error": "mission already done"}

        self.step_count += 1
        reward = self.cfg.reward.per_step_penalty
        info: dict[str, Any] = {"action": Action.NAMES.get(action, "UNKNOWN")}
        r = self.cfg.reward

        # --- Advance weather & roll for new events ---
        assert self.weather is not None and self.events is not None
        self.weather.step()
        new_failures = self.events.step(self.step_count)
        for f in new_failures:
            self._log_event(f"FAILURE: {f.type.name} (dur={f.duration})")
            if f.type.name == "BATTERY_DEGRADATION":
                self.rover.degrade_battery(5.0 * f.severity)
            elif f.type.name == "WHEEL_FAILURE":
                self.rover.damage_rover(3.0 * f.severity)
            elif f.type.name == "ROVER_OVERHEATING":
                self.rover.damage_rover(2.0 * f.severity)
                self.rover.degrade_battery(2.0 * f.severity)

        # --- Apply action ---
        if action in (Action.MOVE_NORTH, Action.MOVE_SOUTH,
                      Action.MOVE_EAST, Action.MOVE_WEST):
            moved, cost = self._try_move(action)
            if moved:
                self.rover.consume("energy", cost)
                reward += r.move_penalty
                self._log_event(f"Rover moved to ({self.rover.x},{self.rover.y}).")
            else:
                reward += r.blocked_move_penalty
                self._log_event(
                    f"Move blocked ({Action.NAMES[action]}) at "
                    f"({self.rover.x},{self.rover.y})."
                )

        elif action == Action.COLLECT_SAMPLE:
            collected, value = self._try_collect()
            if collected:
                self.rover.consume("energy", self.cfg.consumption.per_collect)
                self.rover.degrade_battery(0.3)
                self.rover.damage_rover(0.1)
                reward += r.collect_base_reward + value * r.collect_value_multiplier
                self._log_event(f"Collected sample worth {value}.")
            else:
                reward += r.invalid_action_penalty
                self._log_event("No collectable sample here.")

        elif action == Action.ANALYZE_SAMPLE:
            self.rover.consume("energy", self.cfg.consumption.per_analyze)
            reward += r.analyze_reward
            self._log_event("Analyzed sample.")

        elif action == Action.RETURN_TO_BASE:
            old_pos = (self.rover.x, self.rover.y)
            self._step_toward(self.base.x, self.base.y)
            self.rover.consume("energy", self.cfg.consumption.per_move)
            reward += r.return_to_base_reward
            if (self.rover.x, self.rover.y) != old_pos:
                self._log_event(
                    f"Returning to base: moved to "
                    f"({self.rover.x},{self.rover.y})."
                )
            else:
                self._log_event("Returning to base: path blocked.")

        elif action == Action.RECHARGE:
            if (self.rover.x, self.rover.y) == (self.base.x, self.base.y):
                self.rover.restore("energy", self.base.recharge_rate)
                self.rover.restore("communication", 5.0)
                reward += r.recharge_reward
                self._log_event(
                    f"Recharging at base (energy={self.rover.energy:.1f}%)."
                )
            else:
                reward += r.invalid_action_penalty
                self._log_event("RECHARGE failed: not at base.")

        elif action == Action.REPAIR:
            self.rover.restore("rover_health", 10.0)
            self.rover.restore("battery_health", 5.0)
            self.rover.consume("energy", 2.0)
            reward += r.repair_reward
            self._log_event(
                f"Repaired rover (health={self.rover.rover_health:.1f}%, "
                f"battery={self.rover.battery_health:.1f}%)."
            )

        elif action == Action.COMMUNICATE:
            self.rover.consume("energy", self.cfg.consumption.per_communicate)
            self.rover.communication = 100.0
            self._log_event("Uplink established.")

        elif action == Action.WAIT:
            self.rover.consume("energy", self.cfg.consumption.per_wait)
            self._log_event("Rover waiting.")

        else:
            reward += r.invalid_action_penalty
            info["error"] = "unknown action"
            self._log_event(f"Unknown action: {action}.")

        # --- Passive consumption (life support + slow wear) ---
        self.rover.tick_passive(self.cfg.consumption)

        # --- Weather temperature effects ---
        weather_effects = self.weather.effects()
        self.rover.temperature += weather_effects.temperature_delta
        self.rover.temperature += self.events.temperature_delta()
        self.rover.temperature = max(-100.0, min(100.0, self.rover.temperature))

        # --- Active failures cause ongoing damage ---
        for f in self.events.active:
            if f.type.name == "WHEEL_FAILURE":
                self.rover.damage_rover(0.05 * f.severity)
            elif f.type.name == "ROVER_OVERHEATING":
                self.rover.damage_rover(0.1 * f.severity)
            elif f.type.name == "BATTERY_DEGRADATION":
                self.rover.degrade_battery(0.05 * f.severity)

        # Deep-discharge penalty
        if self.rover.energy < 10.0:
            self.rover.degrade_battery(0.2)

        # --- Comms / water effects from weather & events ---
        if weather_effects.comms_delta > 0:
            self.rover.consume("communication", weather_effects.comms_delta)
        if self.events.comms_lost():
            self.rover.communication = 0.0
        self.rover.consume("water", self.events.water_drain_bonus())

        # --- Guarantee one log line per step ---
        sol_marker = f"[SOL {self.step_count:03d}]"
        if not self.event_log or sol_marker not in self.event_log[-1]:
            self._log_event(f"tick (action={Action.NAMES.get(action, action)})")

        # --- Termination ---
        self._check_termination()

        if self.done:
            reward += r.mission_success_reward if self.success else r.mission_failure_penalty

        return self.get_state(), reward, self.done, info

    # ---------- Action helpers ----------

    def _try_move(self, action: int) -> tuple[bool, float]:
        assert self.rover and self.terrain and self.weather and self.events
        dx, dy = 0, 0
        if action == Action.MOVE_NORTH: dy = -1
        elif action == Action.MOVE_SOUTH: dy = 1
        elif action == Action.MOVE_EAST: dx = 1
        elif action == Action.MOVE_WEST: dx = -1

        nx, ny = self.rover.x + dx, self.rover.y + dy
        if not self.terrain.is_passable(nx, ny):
            return False, 0.0

        self.rover.x, self.rover.y = nx, ny
        terrain_type = self.terrain.get(nx, ny)
        name = TERRAIN_NAMES[terrain_type]
        base_cost = getattr(self.cfg.movement_cost, name, 1.0)

        weather_mult = self.weather.effects().move_cost_multiplier
        event_mult = self.events.move_cost_multiplier()
        cost = base_cost * weather_mult * event_mult

        terrain_damage = {
            "plain": 0.0,
            "sand": 0.02,
            "rock": 0.08,
            "crater": 0.12,
            "mountain": 0.0,
            "base": 0.0,
            "science_site": 0.0,
        }.get(name, 0.0)
        if terrain_damage > 0.0:
            self.rover.damage_rover(terrain_damage)

        if self.rover.energy < 15.0:
            self.rover.degrade_battery(0.15)

        return True, cost

    def _step_toward(self, tx: int, ty: int) -> None:
        """Move one step toward (tx, ty). Tries horizontal first, then vertical."""
        assert self.rover and self.terrain
        dx = 0 if tx == self.rover.x else (1 if tx > self.rover.x else -1)
        dy = 0 if ty == self.rover.y else (1 if ty > self.rover.y else -1)
        for ddx, ddy in [(dx, 0), (0, dy), (dx, dy)]:
            if ddx == 0 and ddy == 0:
                continue
            nx, ny = self.rover.x + ddx, self.rover.y + ddy
            if self.terrain.is_passable(nx, ny):
                self.rover.x, self.rover.y = nx, ny
                return

    def _try_collect(self) -> tuple[bool, int]:
        assert self.rover
        if not self.rover.has_cargo_space():
            return False, 0
        for site in self.science_sites:
            if (site.x, site.y) == (self.rover.x, self.rover.y) and not site.collected:
                site.collected = True
                self.rover.samples_collected += 1
                self.rover.cargo.append(site.sample_type)
                return True, site.value
        return False, 0

    def _check_termination(self) -> None:
        assert self.rover and self.base
        if self.rover.oxygen <= 0:
            self.done, self.success, self.failure_reason = True, False, "Oxygen depleted"
        elif self.rover.energy <= 0:
            self.done, self.success, self.failure_reason = True, False, "Energy depleted"
        elif self.rover.rover_health <= 0:
            self.done, self.success, self.failure_reason = True, False, "Rover destroyed"
        elif self.rover.battery_health <= 0:
            self.done, self.success, self.failure_reason = True, False, "Battery failed"
        elif self.step_count >= self.cfg.mission.max_steps:
            self.done = True
            self.success = self.rover.samples_collected >= self.cfg.mission.success_samples_required
            if not self.success:
                self.failure_reason = "Time limit reached"
        elif self.rover.samples_collected >= self.cfg.mission.success_samples_required:
            if (self.rover.x, self.rover.y) == (self.base.x, self.base.y):
                self.done, self.success = True, True
                self._log_event("Mission success: returned to base with samples.")

    def _log_event(self, msg: str) -> None:
        self.event_log.append(f"[SOL {self.step_count:03d}] {msg}")
        logger.info(msg)

    def active_failures(self) -> list[str]:
        """Return a list of currently-active failure names."""
        if self.events is None:
            return []
        return [f.type.name for f in self.events.active]

    def get_state(self) -> MissionState:
        assert self.terrain and self.rover and self.base
        return MissionState(
            step=self.step_count,
            max_steps=self.cfg.mission.max_steps,
            terrain=self.terrain,
            rover=self.rover,
            base=self.base,
            science_sites=self.science_sites,
            done=self.done,
            success=self.success,
            failure_reason=self.failure_reason,
            events_log=list(self.event_log),
        )