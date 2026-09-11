"""Grid pathfinding for ROVE agents.

Provides breadth-first search (BFS) that navigates around impassable
terrain (mountains). Returns the next cardinal move toward the target.
"""
from __future__ import annotations

from collections import deque

from simulation.environment import Action
from simulation.terrain import Terrain, TerrainType


# Cardinal direction offsets: (dx, dy, action)
MOVES = [
    (0, -1, Action.MOVE_NORTH),
    (0, 1, Action.MOVE_SOUTH),
    (1, 0, Action.MOVE_EAST),
    (-1, 0, Action.MOVE_WEST),
]


def next_step_toward(
    terrain: Terrain,
    start: tuple[int, int],
    target: tuple[int, int],
) -> int:
    """Return the next action to take to walk from `start` toward `target`.

    Uses breadth-first search over passable cells. Returns `Action.WAIT`
    if no path exists (target is unreachable).
    """
    sx, sy = start
    tx, ty = target

    if (sx, sy) == (tx, ty):
        return Action.WAIT

    # BFS from start toward target.
    # We store the FIRST move taken from start, so when we reach the
    # target we know exactly which action got us moving in the right direction.
    visited: set[tuple[int, int]] = {(sx, sy)}
    queue: deque[tuple[int, int, int]] = deque()

    # Seed the queue with the four moves from start.
    for dx, dy, action in MOVES:
        nx, ny = sx + dx, sy + dy
        if (nx, ny) in visited:
            continue
        if not terrain.in_bounds(nx, ny):
            continue
        if not terrain.is_passable(nx, ny):
            continue
        if (nx, ny) == (tx, ty):
            return action
        visited.add((nx, ny))
        queue.append((nx, ny, action))

    # Expand the frontier.
    while queue:
        x, y, first_action = queue.popleft()
        for dx, dy, _ in MOVES:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited:
                continue
            if not terrain.in_bounds(nx, ny):
                continue
            if not terrain.is_passable(nx, ny):
                continue
            if (nx, ny) == (tx, ty):
                return first_action
            visited.add((nx, ny))
            queue.append((nx, ny, first_action))

    # No path found.
    return Action.WAIT