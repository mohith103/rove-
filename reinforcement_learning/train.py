"""Train a PPO agent on ROVE.

Usage:
    python -m reinforcement_learning.train
    python -m reinforcement_learning.train --timesteps 100000 --seed 7
    python -m reinforcement_learning.train --difficulty hard --run-name hard_run
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    CheckpointCallback,
    EvalCallback,
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from reinforcement_learning.callbacks import RoveMetricsCallback
from reinforcement_learning.env import RoveEnv
from simulation.config import load_config, load_config_for_difficulty


MODELS_DIR = Path("reinforcement_learning/models")
LOGS_DIR = Path("reinforcement_learning/logs")
TB_DIR = LOGS_DIR / "tensorboard"


def make_env(seed: int, rank: int = 0, config=None):
    """Factory used by DummyVecEnv. Each parallel env gets a distinct seed."""
    def _init():
        env = RoveEnv(config=config, render_mode=None)
        env.reset(seed=seed + rank)
        return Monitor(env)
    return _init


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=None,
                        help="override config training.timesteps")
    parser.add_argument("--seed", type=int, default=None,
                        help="override config training.seed")
    parser.add_argument("--n-envs", type=int, default=None,
                        help="override config training.n_envs")
    parser.add_argument("--model-path", type=str,
                        default=str(MODELS_DIR / "ppo_rove"),
                        help="where to save the trained model")
    parser.add_argument("--run-name", type=str, default=None,
                        help="suffix for TensorBoard run (default: auto)")
    parser.add_argument("--difficulty", type=str, default="default",
                        choices=["easy", "medium", "hard", "extreme", "default"],
                        help="which difficulty preset to train on")
    args = parser.parse_args()

    # Load config based on difficulty
    cfg = load_config_for_difficulty(args.difficulty)
    tcfg = cfg.training

    timesteps = args.timesteps or tcfg.timesteps
    seed = args.seed if args.seed is not None else tcfg.seed
    n_envs = args.n_envs or tcfg.n_envs

    # Determinism helpers
    np.random.seed(seed)
    torch.manual_seed(seed)

    # Directories
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    TB_DIR.mkdir(parents=True, exist_ok=True)

    run_name = args.run_name or f"ppo_{args.difficulty}_seed{seed}_steps{timesteps}"

    print("=" * 60)
    print(f"Training PPO on ROVE")
    print(f"  difficulty: {args.difficulty}")
    print(f"  timesteps : {timesteps:,}")
    print(f"  seed      : {seed}")
    print(f"  n_envs    : {n_envs}")
    print(f"  run name  : {run_name}")
    print("=" * 60)

    # Vectorized training env
    train_env = DummyVecEnv([
        make_env(seed, i, config=cfg) for i in range(n_envs)
    ])

    # Separate evaluation env (single, deterministic seed)
    eval_env = DummyVecEnv([make_env(seed + 10_000, 0, config=cfg)])

    # PPO model
    model = PPO(
        policy="MlpPolicy",
        env=train_env,
        learning_rate=tcfg.learning_rate,
        n_steps=tcfg.n_steps,
        batch_size=tcfg.batch_size,
        gamma=tcfg.gamma,
        gae_lambda=tcfg.gae_lambda,
        clip_range=tcfg.clip_range,
        ent_coef=tcfg.ent_coef,
        vf_coef=tcfg.vf_coef,
        max_grad_norm=tcfg.max_grad_norm,
        policy_kwargs=dict(net_arch=dict(pi=tcfg.net_arch, vf=tcfg.net_arch)),
        tensorboard_log=str(TB_DIR),
        verbose=1,
        seed=seed,
    )

    # Callbacks
    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path=str(MODELS_DIR / "best"),
        log_path=str(LOGS_DIR / "eval"),
        eval_freq=max(1, tcfg.eval_freq // n_envs),
        n_eval_episodes=tcfg.eval_episodes,
        deterministic=True,
        render=False,
    )
    checkpoint_cb = CheckpointCallback(
        save_freq=max(1, tcfg.save_freq // n_envs),
        save_path=str(MODELS_DIR / "checkpoints"),
        name_prefix=f"ppo_rove_{args.difficulty}",
    )
    metrics_cb = RoveMetricsCallback()

    start = time.time()
    model.learn(
        total_timesteps=timesteps,
        callback=[eval_cb, checkpoint_cb, metrics_cb],
        tb_log_name=run_name,
        progress_bar=False,
    )
    elapsed = time.time() - start

    # Save final
    final_path = Path(args.model_path)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(final_path))
    print(f"\nTraining finished in {elapsed/60:.1f} minutes.")
    print(f"Saved model to {final_path}.zip")
    print(f"TensorBoard logs in {TB_DIR}")
    print(f"\nTo view charts:\n  tensorboard --logdir {TB_DIR}")


if __name__ == "__main__":
    main()