"""Print the observation vector for a few random steps.

Great for verifying the wrapper is doing what you expect.
Now handles the 66-dimensional observation (17 scalars + 35 terrain +
5 weather + 8 failure flags + 1 weather_remaining).

Usage:
    python -m experiments.peek_observation
"""
from __future__ import annotations

import numpy as np

from reinforcement_learning.env import RoveEnv


FEATURE_NAMES = [
    "rover_x", "rover_y",
    "base_x", "base_y",
    "distance_to_base",
    "distance_to_nearest_site",
    "energy", "water", "oxygen", "food",
    "battery_health", "rover_health",
    "communication", "temperature",
    "samples_progress", "steps_remaining_fraction",
    "cargo_fraction",
    # Then 35 terrain slots (5 blocks × 7)
]

TERRAIN_LABELS = ["plain", "rock", "crater", "mountain", "sand", "base", "site"]
DIRECTIONS = ["under", "north", "south", "east", "west"]

WEATHER_LABELS = ["clear", "dusty", "dust_storm", "cold_snap", "extreme_cold"]
FAILURE_LABELS = [
    "none", "solar", "wheel", "battery",
    "comms", "navigation", "water_leak", "overheat",
]


def name_for_index(i: int) -> str:
    """Return a human-readable name for observation slot `i`."""
    n = len(FEATURE_NAMES)
    if i < n:
        return FEATURE_NAMES[i]
    i -= n
    # terrain block (35 = 5 blocks × 7 terrain types)
    if i < 35:
        block = i // 7
        terrain = TERRAIN_LABELS[i % 7]
        return f"terrain_{DIRECTIONS[block]}_{terrain}"
    i -= 35
    # weather block (5)
    if i < 5:
        return f"weather_{WEATHER_LABELS[i]}"
    i -= 5
    # failure block (8)
    if i < 8:
        return f"failure_{FAILURE_LABELS[i]}"
    i -= 8
    # weather remaining
    return "weather_remaining"


def main() -> None:
    env = RoveEnv()
    obs, info = env.reset(seed=42)
    print(f"Observation dim: {obs.shape[0]}")
    print(f"Action space   : {env.action_space.n} actions")
    print()

    for step in range(3):
        action = int(np.random.default_rng(step).integers(0, env.action_space.n))
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"--- Step {step + 1} | action={info['action']} "
              f"reward={reward:+.3f} ---")
        # Print all slots (skip the big terrain block for readability)
        for i, v in enumerate(obs):
            name = name_for_index(i)
            # Always print scalar features; for terrain print only the "under"
            # block that is nonzero and the neighbors as a summary
            if i < len(FEATURE_NAMES):
                print(f"  {i:>3} {name:<32} {v:+.3f}")
            elif name.startswith("terrain_under") or name.startswith("terrain_north") \
                    or name.startswith("terrain_south") or name.startswith("terrain_east") \
                    or name.startswith("terrain_west"):
                if abs(v) > 1e-6:  # only print the active terrain type per direction
                    print(f"  {i:>3} {name:<32} {v:+.3f}")
            elif i >= len(FEATURE_NAMES) + 35:  # weather + failures + remaining
                print(f"  {i:>3} {name:<32} {v:+.3f}")
        print()


if __name__ == "__main__":
    main()