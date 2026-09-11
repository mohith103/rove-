"""Basic tests for the ROVE environment."""
from __future__ import annotations

from simulation.environment import Action, MarsEnvironment
from simulation.terrain import TerrainType


def test_reset_creates_world():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    assert state.rover is not None
    assert state.base is not None
    assert len(state.science_sites) == env.cfg.science.num_sites


def test_reset_is_deterministic():
    env1 = MarsEnvironment()
    s1 = env1.reset(seed=42)
    env2 = MarsEnvironment()
    s2 = env2.reset(seed=42)
    assert (s1.rover.x, s1.rover.y) == (s2.rover.x, s2.rover.y)
    assert [(s.x, s.y, s.value) for s in s1.science_sites] == \
           [(s.x, s.y, s.value) for s in s2.science_sites]


def test_movement_consumes_energy():
    env = MarsEnvironment()
    env.reset(seed=42)
    start_energy = env.rover.energy
    env.step(Action.MOVE_EAST)
    assert env.rover.energy < start_energy


def test_blocked_by_mountain():
    env = MarsEnvironment()
    env.reset(seed=42)
    env.terrain.set(env.rover.x + 1, env.rover.y, TerrainType.MOUNTAIN)
    start = (env.rover.x, env.rover.y)
    env.step(Action.MOVE_EAST)
    assert (env.rover.x, env.rover.y) == start


def test_collect_sample():
    env = MarsEnvironment()
    env.reset(seed=42)
    site = env.science_sites[0]
    env.rover.x, env.rover.y = site.x, site.y
    _, reward, _, _ = env.step(Action.COLLECT_SAMPLE)
    assert env.rover.samples_collected == 1
    assert reward > 0


def test_oxygen_depletion_ends_mission():
    env = MarsEnvironment()
    env.reset(seed=42)
    env.rover.oxygen = 0.01
    env.step(Action.WAIT)
    assert env.done is True
    assert env.success is False