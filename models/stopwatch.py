from __future__ import annotations

import time


class Stopwatch:
    """Stopwatch state machine based on monotonic time."""

    def __init__(self) -> None:
        self._state = "idle"
        self._started_at = 0.0
        self._elapsed_before_start = 0.0

    @property
    def state(self) -> str:
        return self._state

    def start(self) -> None:
        self._state = "running"
        self._started_at = time.monotonic()
        self._elapsed_before_start = 0.0

    def pause(self) -> None:
        if self._state != "running":
            return
        self._elapsed_before_start = self.elapsed_seconds()
        self._state = "paused"

    def resume(self) -> None:
        if self._state != "paused":
            return
        self._started_at = time.monotonic()
        self._state = "running"

    def reset(self) -> None:
        self._state = "idle"
        self._started_at = 0.0
        self._elapsed_before_start = 0.0

    def elapsed_seconds(self) -> float:
        if self._state == "running":
            return self._elapsed_before_start + time.monotonic() - self._started_at
        return self._elapsed_before_start

    def progress_fraction(self) -> float:
        return (self.elapsed_seconds() % 60) / 60

    def formatted_time(self) -> str:
        total_tenths = int(self.elapsed_seconds() * 10)
        tenths = total_tenths % 10
        total_seconds = total_tenths // 10
        seconds = total_seconds % 60
        minutes = (total_seconds // 60) % 60
        hours = total_seconds // 3600
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{tenths}"
