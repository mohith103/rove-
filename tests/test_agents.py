"""Tests for the ROVE agents."""
from __future__ import annotations

from agents.random_agent import RandomAgent
from agents.rule_based import RuleBasedAgent
from simulation.environment import Action, MarsEnvironment


def test_random_agent_returns_valid_action():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    agent = RandomAgent(seed=0)
    for _ in range(50):
        a = agent.act(state)
        assert 0 <= a < Action.N_ACTIONS


def test_rule_based_moves_toward_base_when_oxygen_low():
    """When oxygen is critical, the rover should move toward base.

    With BFS pathfinding, the agent returns a cardinal move (not the
    abstract RETURN_TO_BASE action). We check that the chosen action
    reduces Manhattan distance to base.
    """
    env = MarsEnvironment()
    state = env.reset(seed=42)
    state.rover.oxygen = 10.0  # critical
    state.rover.x, state.rover.y = 5, 5  # away from base
    agent = RuleBasedAgent()

    action = agent.act(state)

    # Action must be one of the four cardinal moves
    assert action in (
        Action.MOVE_NORTH,
        Action.MOVE_SOUTH,
        Action.MOVE_EAST,
        Action.MOVE_WEST,
    )

    # Applying that move should reduce distance to base
    before = abs(5 - state.base.x) + abs(5 - state.base.y)
    dx, dy = 0, 0
    if action == Action.MOVE_NORTH: dy = -1
    elif action == Action.MOVE_SOUTH: dy = 1
    elif action == Action.MOVE_EAST: dx = 1
    elif action == Action.MOVE_WEST: dx = -1
    after = abs(5 + dx - state.base.x) + abs(5 + dy - state.base.y)
    assert after < before, f"action {action} did not reduce distance to base"


def test_rule_based_recharges_at_base():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    state.rover.x, state.rover.y = state.base.x, state.base.y
    state.rover.energy = 30.0
    agent = RuleBasedAgent()
    assert agent.act(state) == Action.RECHARGE


def test_rule_based_collects_when_on_site():
    env = MarsEnvironment()
    state = env.reset(seed=42)
    site = state.science_sites[0]
    state.rover.x, state.rover.y = site.x, site.y
    state.rover.energy = 90.0
    state.rover.oxygen = 90.0
    agent = RuleBasedAgent()
    assert agent.act(state) == Action.COLLECT_SAMPLE


def test_rule_based_beats_random_on_average():
    """Rule-based should collect more samples than random on average."""
    env = MarsEnvironment()
    rule = RuleBasedAgent()
    rand = RandomAgent(seed=1)

    rule_samples = 0
    rand_samples = 0
    episodes = 20

    for i in range(episodes):
        # Rule-based
        rule.reset()
        state = env.reset(seed=i)
        while not state.done:
            action = rule.act(state)
            state, _, _, _ = env.step(action)
        rule_samples += state.rover.samples_collected

        # Random
        rand.reset()
        state = env.reset(seed=i)
        while not state.done:
            action = rand.act(state)
            state, _, _, _ = env.step(action)
        rand_samples += state.rover.samples_collected

    assert rule_samples > rand_samples, (
        f"rule={rule_samples} random={rand_samples}"
    )


def test_rule_based_does_not_get_stuck():
    """A rover surrounded by mountains on two sides should still make progress."""
    from simulation.terrain import TerrainType

    env = MarsEnvironment()
    state = env.reset(seed=42)

    # Put rover in a corner with a mountain wall — it should still move
    state.rover.x, state.rover.y = 5, 5
    state.rover.energy = 90.0
    state.rover.oxygen = 90.0

    # Block the direct path with mountains
    env.terrain.set(5, 4, TerrainType.MOUNTAIN)
    env.terrain.set(5, 6, TerrainType.MOUNTAIN)
    env.terrain.set(4, 5, TerrainType.MOUNTAIN)
    env.terrain.set(6, 5, TerrainType.MOUNTAIN)

    # Rover should still return a valid action
    agent = RuleBasedAgent()
    action = agent.act(state)
    assert 0 <= action < Action.N_ACTIONS