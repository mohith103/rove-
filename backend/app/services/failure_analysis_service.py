"""Mission failure analysis."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CriticalMoment:
    step: int
    label: str
    detail: str
    severity: str


def _format_event(ev: str) -> str:
    if ev.startswith("[SOL") and "]" in ev:
        return ev.split("]", 1)[1].strip()
    return ev


def analyze_mission(mission) -> dict[str, Any]:
    if mission.state is None:
        return {
            "mission_id": mission.id,
            "success": False,
            "primary_cause": "unknown",
            "contributing_factors": [],
            "recommendations": [],
            "critical_moments": [],
            "summary": "No mission state available.",
        }

    frames = mission.frames or []
    events = mission.events or []
    state = mission.state
    success = state.success
    failure_reason = state.failure_reason

    critical_moments: list[CriticalMoment] = []
    contributing: list[str] = []
    recommendations: list[str] = []

    first_low_energy = None
    first_low_oxygen = None
    first_low_health = None
    first_low_battery = None
    total_low_energy_steps = 0
    total_low_oxygen_steps = 0

    for frame in frames:
        rover = frame["rover"]
        step = frame["step"]

        if rover["energy"] < 30 and first_low_energy is None:
            first_low_energy = step
        if rover["energy"] < 20:
            total_low_energy_steps += 1

        if rover["oxygen"] < 40 and first_low_oxygen is None:
            first_low_oxygen = step
        if rover["oxygen"] < 25:
            total_low_oxygen_steps += 1

        if rover["rover_health"] < 60 and first_low_health is None:
            first_low_health = step
        if rover["battery_health"] < 60 and first_low_battery is None:
            first_low_battery = step

    failure_events = [e for e in events if "FAILURE:" in e]
    failure_event_types: dict[str, int] = {}
    for e in failure_events:
        try:
            name = e.split("FAILURE:", 1)[1].strip().split(" ")[0]
            failure_event_types[name] = failure_event_types.get(name, 0) + 1
        except IndexError:
            pass

    if first_low_energy is not None:
        critical_moments.append(CriticalMoment(
            step=first_low_energy,
            label="Energy below 30%",
            detail=f"Energy first dropped below 30% at SOL {first_low_energy}.",
            severity="warning",
        ))
    if first_low_oxygen is not None:
        critical_moments.append(CriticalMoment(
            step=first_low_oxygen,
            label="Oxygen below 40%",
            detail=f"Oxygen first dropped below 40% at SOL {first_low_oxygen}.",
            severity="warning",
        ))
    if first_low_health is not None:
        critical_moments.append(CriticalMoment(
            step=first_low_health,
            label="Rover health below 60%",
            detail=f"Rover health first dropped below 60% at SOL {first_low_health}.",
            severity="warning",
        ))
    if first_low_battery is not None:
        critical_moments.append(CriticalMoment(
            step=first_low_battery,
            label="Battery health below 60%",
            detail=f"Battery health first dropped below 60% at SOL {first_low_battery}.",
            severity="info",
        ))

    for e in failure_events[:8]:
        try:
            sol = int(e[5:8])
        except (ValueError, IndexError):
            sol = 0
        critical_moments.append(CriticalMoment(
            step=sol,
            label="Equipment failure",
            detail=_format_event(e),
            severity="critical",
        ))

    critical_moments.sort(key=lambda m: m.step)

    if success:
        primary_cause = "No failure — mission succeeded."
    elif failure_reason == "Energy depleted":
        primary_cause = (
            f"Energy depletion at SOL {state.step}. "
            f"The rover ran out of power while still away from base."
        )
        contributing.append("Energy was below 30% for a long stretch.")
        recommendations.append(
            "Return to base when energy drops below 35%, especially during "
            "dust storms."
        )
    elif failure_reason == "Oxygen depleted":
        primary_cause = (
            f"Oxygen depletion at SOL {state.step}. "
            f"Life support ran out before the rover returned home."
        )
        recommendations.append(
            "Prioritize returning to base when oxygen drops below 30%."
        )
    elif failure_reason == "Rover destroyed":
        primary_cause = (
            f"Rover destruction at SOL {state.step}. "
            f"Component damage exceeded safe limits."
        )
        recommendations.append(
            "Repair the rover when health drops below 50%."
        )
    elif failure_reason == "Battery failed":
        primary_cause = (
            f"Battery failure at SOL {state.step}. "
            f"Permanent wear exceeded safe limits."
        )
        recommendations.append(
            "Reduce deep discharge cycles: recharge before energy falls below 20%."
        )
    elif failure_reason == "Time limit reached":
        primary_cause = (
            f"Time limit reached at SOL {state.step}. "
            f"The rover did not collect enough samples in time."
        )
        recommendations.append(
            "Target the nearest high-value science site first."
        )
    else:
        primary_cause = f"Mission failed: {failure_reason or 'unknown reason'}."

    if total_low_energy_steps > 10:
        contributing.append(
            f"Energy was below 20% for {total_low_energy_steps} SOLs."
        )
    if total_low_oxygen_steps > 10:
        contributing.append(
            f"Oxygen was below 25% for {total_low_oxygen_steps} SOLs."
        )
    if "DUST_STORM" in " ".join(events):
        contributing.append("Dust storm occurred during the mission.")
    if failure_event_types:
        summary_events = ", ".join(f"{k} x{v}" for k, v in failure_event_types.items())
        contributing.append(f"Equipment failures: {summary_events}.")
    if state.failure_reason and "Time limit" in state.failure_reason:
        contributing.append("Mission time budget was exhausted.")

    if first_low_energy is not None and not success:
        recommendations.append(
            f"Consider an earlier return-to-base: energy first dropped below "
            f"30% at SOL {first_low_energy}."
        )
    if first_low_health is not None and first_low_health < state.step:
        recommendations.append(
            f"Perform repairs earlier — rover health first dropped below 60% "
            f"at SOL {first_low_health}."
        )
    if "WHEEL_FAILURE" in failure_event_types:
        recommendations.append(
            "Avoid rock and crater terrain after a wheel failure — movement "
            "costs double."
        )
    if not recommendations:
        recommendations.append(
            "Mission completed successfully. No changes recommended."
        )

    if success:
        summary = (
            f"Mission succeeded at SOL {state.step}. "
            f"{state.rover.samples_collected} sample(s) collected. "
            f"{len(failure_events)} equipment failure(s) encountered."
        )
    else:
        summary = (
            f"Mission failed at SOL {state.step} due to: {failure_reason}. "
            f"{len(critical_moments)} critical moment(s) identified."
        )

    return {
        "mission_id": mission.id,
        "success": success,
        "primary_cause": primary_cause,
        "contributing_factors": contributing,
        "recommendations": recommendations,
        "critical_moments": [
            {
                "step": m.step,
                "label": m.label,
                "detail": m.detail,
                "severity": m.severity,
            }
            for m in critical_moments
        ],
        "summary": summary,
    }
