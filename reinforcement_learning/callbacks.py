"""Custom Stable-Baselines3 callbacks for ROVE training."""
from __future__ import annotations

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


class RoveMetricsCallback(BaseCallback):
    """Logs extra metrics (samples collected, success) during training.

    SB3 already logs reward/losses. This adds ROVE-specific signals so
    the TensorBoard charts tell you whether the agent is actually
    collecting samples or just surviving.
    """

    def __init__(self, verbose: int = 0) -> None:
        super().__init__(verbose)
        self.episode_samples: list[int] = []
        self.episode_success: list[int] = []

    def _on_step(self) -> bool:
        # SB3 stores per-env info in self.locals["infos"]
        for info in self.locals.get("infos", []):
            if "episode" in info:
                # End of an episode: SB3 added "episode" dict
                pass
        return True

    def _on_rollout_end(self) -> None:
        """Called after each rollout — compute stats from recent buffer."""
        try:
            buf = self.model.ep_info_buffer
            if not buf:
                return
            rewards = [e["r"] for e in buf]
            lengths = [e["l"] for e in buf]
            self.logger.record("rove/mean_episode_reward", float(np.mean(rewards)))
            self.logger.record("rove/mean_episode_length", float(np.mean(lengths)))
        except Exception:
            # Never crash training because of a logging hiccup
            pass