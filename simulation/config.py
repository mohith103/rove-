"""Configuration loader for the ROVE simulation."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class MapConfig(BaseModel):
    width: int = 20
    height: int = 20
    seed: int = 42


class TerrainConfig(BaseModel):
    plain: float = 0.55
    rock: float = 0.15
    crater: float = 0.10
    mountain: float = 0.05
    sand: float = 0.15


class MovementCostConfig(BaseModel):
    plain: float = 1.0
    rock: float = 2.0
    crater: float = 2.5
    mountain: float = 3.5
    sand: float = 1.5


class RoverConfig(BaseModel):
    initial_energy: float = 100.0
    initial_water: float = 80.0
    initial_oxygen: float = 90.0
    initial_food: float = 100.0
    initial_battery_health: float = 100.0
    initial_rover_health: float = 100.0
    cargo_capacity: int = 5


class ConsumptionConfig(BaseModel):
    per_move: float = 1.0
    per_collect: float = 3.0
    per_analyze: float = 5.0
    per_communicate: float = 1.0
    per_wait: float = 0.2
    water_per_tick: float = 0.05
    oxygen_per_tick: float = 0.03
    food_per_tick: float = 0.02
    battery_degradation_per_tick: float = 0.02
    rover_health_degradation_per_tick: float = 0.01


class BaseConfig(BaseModel):
    x: int = 0
    y: int = 0
    recharge_rate: float = 10.0


class ScienceConfig(BaseModel):
    num_sites: int = 5
    min_value: int = 50
    max_value: int = 200
    min_difficulty: int = 1
    max_difficulty: int = 5


class MissionConfig(BaseModel):
    max_steps: int = 200
    success_samples_required: int = 3


class RewardConfig(BaseModel):
    per_step_penalty: float = -0.05
    move_penalty: float = -0.1
    blocked_move_penalty: float = -0.5
    collect_base_reward: float = 100.0
    collect_value_multiplier: float = 0.5
    analyze_reward: float = 5.0
    return_to_base_reward: float = 0.0
    recharge_reward: float = 0.0
    repair_reward: float = 0.0
    invalid_action_penalty: float = -1.0
    mission_success_reward: float = 500.0
    mission_failure_penalty: float = -1000.0

class TrainingConfig(BaseModel):
    timesteps: int = 200_000
    seed: int = 42
    n_envs: int = 4
    learning_rate: float = 3e-4
    n_steps: int = 1024
    batch_size: int = 64
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    net_arch: list[int] = Field(default_factory=lambda: [64, 64])
    eval_episodes: int = 20
    eval_freq: int = 10_000
    save_freq: int = 50_000

class WeatherConfig(BaseModel):
    change_probability: float = 0.02
    probabilities: dict[str, float] = Field(default_factory=lambda: {
        "clear": 0.55, "dusty": 0.20, "dust_storm": 0.15,
        "cold_snap": 0.07, "extreme_cold": 0.03,
    })
    duration: dict[str, list[int]] = Field(default_factory=lambda: {
        "clear": [1, 5], "moderate": [5, 15], "severe": [10, 25],
    })


class EventsConfig(BaseModel):
    base_probability: float = 0.01
    probabilities: dict[str, float] = Field(default_factory=lambda: {
        "solar_panel_failure": 0.15,
        "wheel_failure": 0.20,
        "battery_degradation": 0.10,
        "communication_loss": 0.15,
        "navigation_sensor_failure": 0.10,
        "water_leak": 0.15,
        "rover_overheating": 0.15,
    })

class RoveConfig(BaseModel):
    """Top-level ROVE config object."""
    map: MapConfig = Field(default_factory=MapConfig)
    terrain: TerrainConfig = Field(default_factory=TerrainConfig)
    movement_cost: MovementCostConfig = Field(default_factory=MovementCostConfig)
    rover: RoverConfig = Field(default_factory=RoverConfig)
    consumption: ConsumptionConfig = Field(default_factory=ConsumptionConfig)
    base: BaseConfig = Field(default_factory=BaseConfig)
    science: ScienceConfig = Field(default_factory=ScienceConfig)
    mission: MissionConfig = Field(default_factory=MissionConfig)
    reward: RewardConfig = Field(default_factory=RewardConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    weather: WeatherConfig = Field(default_factory=WeatherConfig)
    events: EventsConfig = Field(default_factory=EventsConfig)


def load_config(path: str | Path = "configs/default.yaml") -> RoveConfig:
    """Load config from a YAML file."""
    with open(path, "r") as f:
        raw: dict[str, Any] = yaml.safe_load(f)
    return RoveConfig(**raw)

DIFFICULTY_FILES = {
    "easy": "configs/easy.yaml",
    "medium": "configs/medium.yaml",
    "hard": "configs/hard.yaml",
    "extreme": "configs/extreme.yaml",
    "default": "configs/default.yaml",
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base (override wins)."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config_for_difficulty(difficulty: str) -> RoveConfig:
    """Load default.yaml, then overlay the difficulty file's overrides.

    Args:
        difficulty: one of easy, medium, hard, extreme, default.
    """
    if difficulty not in DIFFICULTY_FILES:
        raise ValueError(f"unknown difficulty {difficulty!r}")

    with open("configs/default.yaml", "r") as f:
        base = yaml.safe_load(f)

    diff_path = DIFFICULTY_FILES[difficulty]
    if difficulty != "default":
        with open(diff_path, "r") as f:
            override = yaml.safe_load(f) or {}
        # Ignore the "defaults" key (it's documentation for humans)
        override.pop("defaults", None)
        base = _deep_merge(base, override)

    return RoveConfig(**base)