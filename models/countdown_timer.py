from __future__ import annotations

import time


class CountdownTimer:
    """Countdown timer state machine with pause, resume, and finish detection."""

    def __init__(self) -> None:
        self._duration_seconds = 0
        self._remaining_before_start = 0.0
        self._started_at = 0.0
        self._state = "idle"
        self._finish_reported = False

    @property
    def state(self) -> str:
        return self._state

    @property
    def duration_seconds(self) -> int:
        return self._duration_seconds

    def set_duration(self, minutes: int, seconds: int) -> None:
        if minutes < 0 or seconds < 0:
            raise ValueError("Timer values must be non-negative.")
        if seconds > 59:
            raise ValueError("Seconds must be between 0 and 59.")

        total_seconds = minutes * 60 + seconds
        if total_seconds <= 0:
            raise ValueError("Timer duration must be greater than zero.")

        self._duration_seconds = total_seconds
        self._remaining_before_start = float(total_seconds)
        self._started_at = 0.0
        self._state = "idle"
        self._finish_reported = False

    def start(self) -> None:
        if self._duration_seconds <= 0:
            raise ValueError("Timer duration must be configured first.")

        self._remaining_before_start = float(self._duration_seconds)
        self._started_at = time.monotonic()
        self._state = "running"
        self._finish_reported = False

    def pause(self) -> None:
        if self._state != "running":
            return
        self._remaining_before_start = self.remaining_seconds()
        self._state = "paused"

    def resume(self) -> None:
        if self._state != "paused":
            return
        self._started_at = time.monotonic()
        self._state = "running"

    def reset(self) -> None:
        self._remaining_before_start = float(self._duration_seconds)
        self._started_at = 0.0
        self._state = "idle"
        self._finish_reported = False

    def remaining_seconds(self) -> float:
        if self._duration_seconds <= 0:
            return 0.0

        if self._state == "running":
            elapsed = time.monotonic() - self._started_at
            return max(0.0, self._remaining_before_start - elapsed)

        return max(0.0, self._remaining_before_start)

    def progress_fraction(self) -> float:
        if self._duration_seconds <= 0:
            return 0.0
        elapsed = self._duration_seconds - self.remaining_seconds()
        return min(1.0, max(0.0, elapsed / self._duration_seconds))

    def consume_finished(self) -> bool:
        if self._state != "running" or self.remaining_seconds() > 0:
            return False
        if self._finish_reported:
            return False

        self._state = "finished"
        self._finish_reported = True
        return True

    def formatted_time(self) -> str:
        total_seconds = int(self.remaining_seconds() + 0.999)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
