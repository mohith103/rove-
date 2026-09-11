"""Smoke test: verify PPO can train for a tiny number of steps.

This is NOT meant to produce a good agent. It only proves the training
pipeline is wired correctly. Runs in ~10 seconds.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

from reinforcement_learning.env import RoveEnv


def _make_env():
    def _init():
        return RoveEnv()
    return _init


def test_ppo_can_train_tiny(tmp_path: Path):
    env = DummyVecEnv([_make_env()])
    model = PPO(
        "MlpPolicy",
        env,
        n_steps=64,
        batch_size=32,
        n_epochs=2,
        learning_rate=1e-3,
        verbose=0,
        seed=0,
    )
    model.learn(total_timesteps=512)

    # Save + load
    out = tmp_path / "smoke_model"
    model.save(str(out))
    assert (out.parent / f"{out.name}.zip").exists()

    loaded = PPO.load(str(out))
    obs = env.reset()
    action, _ = loaded.predict(obs, deterministic=True)
    assert int(action[0]) in range(11)


def test_model_survives_a_full_episode(tmp_path: Path):
    env = DummyVecEnv([_make_env()])
    model = PPO("MlpPolicy", env, n_steps=64, batch_size=32, verbose=0, seed=1)
    model.learn(total_timesteps=256)

    obs = env.reset()
    for _ in range(300):
        action, _ = model.predict(obs, deterministic=True)
        obs, _, dones, _ = env.step(action)
        if dones[0]:
            break
    assert True  # If we got here without error, pass