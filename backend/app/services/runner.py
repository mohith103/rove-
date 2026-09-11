"""Background mission runner.

A simple daemon thread per mission. Kept deliberately small — if you later
want proper async, swap for asyncio tasks.
"""
from __future__ import annotations

import threading
import time

from backend.app.config import settings
from backend.app.services.mission_service import Mission


class MissionRunner:
    """Runs a mission in a background thread until it completes."""

    def __init__(self, mission: Mission, speed: float = 1.0) -> None:
        self.mission = mission
        self.speed = max(0.1, speed)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    # ------------------------------------------------------------------ #

    def _loop(self) -> None:
        interval = settings.stream_interval / self.speed
        steps_per_tick = max(1, settings.stream_steps_per_tick)

        while not self._stop.is_set():
            if self.mission.status == "done":
                break
            if self.mission.status == "running":
                for _ in range(steps_per_tick):
                    self.mission.step_once()
                    if self.mission.status == "done":
                        break
            time.sleep(interval)