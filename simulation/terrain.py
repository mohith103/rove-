"""Mars terrain: grid generation for ROVE."""
from __future__ import annotations

from enum import IntEnum

import numpy as np


class TerrainType(IntEnum):
    PLAIN = 0
    ROCK = 1
    CRATER = 2
    MOUNTAIN = 3
    SAND = 4
    BASE = 5
    SCIENCE_SITE = 6


TERRAIN_NAMES: dict[TerrainType, str] = {
    TerrainType.PLAIN: "plain",
    TerrainType.ROCK: "rock",
    TerrainType.CRATER: "crater",
    TerrainType.MOUNTAIN: "mountain",
    TerrainType.SAND: "sand",
    TerrainType.BASE: "base",
    TerrainType.SCIENCE_SITE: "science_site",
}


class Terrain:
    """2D Mars terrain grid. grid[y, x] -> TerrainType."""

    def __init__(self, width: int, height: int, seed: int = 42) -> None:
        self.width = width
        self.height = height
        self.rng = np.random.default_rng(seed)
        self.grid = np.full((height, width), TerrainType.PLAIN, dtype=np.int8)

    def generate(self, distribution: dict[str, float]) -> None:
        names = ["plain", "rock", "crater", "mountain", "sand"]
        probs = np.array([distribution[n] for n in names], dtype=np.float64)
        probs = probs / probs.sum()
        flat_size = self.width * self.height
        choices = self.rng.choice(len(names), size=flat_size, p=probs)
        self.grid = choices.reshape((self.height, self.width)).astype(np.int8)

    def get(self, x: int, y: int) -> TerrainType:
        if not self.in_bounds(x, y):
            return TerrainType.MOUNTAIN
        return TerrainType(int(self.grid[y, x]))

    def set(self, x: int, y: int, t: TerrainType) -> None:
        if self.in_bounds(x, y):
            self.grid[y, x] = int(t)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_passable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        return self.get(x, y) != TerrainType.MOUNTAIN

    def to_list(self) -> list[list[int]]:
        return self.grid.tolist()