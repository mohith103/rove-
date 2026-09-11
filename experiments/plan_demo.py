"""Show how the planner scores plans under different mission modes."""
from __future__ import annotations

from agents.planner import Planner
from simulation.config import load_config
from simulation.environment import MarsEnvironment


def main() -> None:
    cfg = load_config()
    env = MarsEnvironment(cfg)
    state = env.reset(seed=42)

    # Simulate a low-energy situation to make modes diverge
    state.rover.energy = 22.0
    state.rover.x, state.rover.y = 8, 8

    for mode in ["science", "survival", "exploration", "balanced"]:
        planner = Planner(mode=mode)
        best, scored = planner.choose(state)
        print(f"\n=== MODE: {mode.upper()} ===")
        print(f"weights: {planner.weights.to_dict()}")
        print(f"CHOSEN: {best.name}  (action={best.action}, score={scored[0][1]:+.2f})")
        print("ALL PLANS:")
        for p, s in scored:
            print(f"  {p.name:<28} score={s:+8.2f}  "
                  f"science={p.expected_science:6.1f}  "
                  f"energy={p.expected_energy_cost:6.1f}  "
                  f"risk={p.expected_risk:5.2f}")


if __name__ == "__main__":
    main()