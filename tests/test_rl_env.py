"""Tests for the Gymnasium wrapper."""
from __future__ import annotations

import numpy as np
from gymnasium.utils.env_checker import check_env

from reinforcement_learning.env import RoveEnv, _obs_dim
from simulation.config import load_config


def test_check_env_passes():
    """Gymnasium's own checker validates our env."""
    env = RoveEnv()
    check_env(env, skip_render_check=True)


def test_observation_shape_matches_space():
    env = RoveEnv()
    obs, _ = env.reset(seed=42)
    assert obs.shape == env.observation_space.shape
    assert obs.dtype == np.float32


def test_observation_is_normalized():
    env = RoveEnv()
    obs, _ = env.reset(seed=42)
    assert np.all(obs >= -1.0 - 1e-6)
    assert np.all(obs <= 1.0 + 1e-6)


def test_action_space_size():
    env = RoveEnv()
    assert env.action_space.n == 11


def test_step_returns_five_values():
    env = RoveEnv()
    env.reset(seed=42)
    result = env.step(0)
    assert len(result) == 5
    obs, reward, terminated, truncated, info = result
    assert obs.shape == env.observation_space.shape
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_reset_is_deterministic():
    env1 = RoveEnv()
    o1, _ = env1.reset(seed=42)
    env2 = RoveEnv()
    o2, _ = env2.reset(seed=42)
    assert np.allclose(o1, o2)


def test_episode_terminates_or_truncates():
    env = RoveEnv()
    env.reset(seed=0)
    done = False
    steps = 0
    while not done and steps < 500:
        _, _, terminated, truncated, _ = env.step(0)  # always MOVE_NORTH
        done = terminated or truncated
        steps += 1
    assert done
    assert steps <= 500


def test_observation_dim_consistent():
    env = RoveEnv()
    expected = _obs_dim(env.cfg)
    assert env.observation_space.shape == (expected,)