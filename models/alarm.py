from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Alarm:
    """Alarm value object with validation and one-trigger-per-day behavior."""

    hour: int
    minute: int
    enabled: bool = True
    triggered_date: Optional[date] = None

    def __post_init__(self) -> None:
        if not 0 <= self.hour <= 23:
            raise ValueError("Hour must be between 0 and 23.")
        if not 0 <= self.minute <= 59:
            raise ValueError("Minute must be between 0 and 59.")

    def formatted_time(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def should_trigger(self, moment: datetime) -> bool:
        if not self.enabled:
            return False
        if self.triggered_date == moment.date():
            return False
        return self.hour == moment.hour and self.minute == moment.minute

    def mark_triggered(self, moment: datetime) -> None:
        self.triggered_date = moment.date()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
