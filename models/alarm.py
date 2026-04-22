from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Alarm:
    """Alarm value object with validation, trigger, and snooze behavior."""

    hour: int
    minute: int
    enabled: bool = True
    last_trigger_key: Optional[str] = None
    snooze_until: Optional[datetime] = None

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

        trigger_key = self._trigger_key(moment)
        if self.last_trigger_key == trigger_key:
            return False

        if self.snooze_until is not None:
            return moment >= self.snooze_until

        return self.hour == moment.hour and self.minute == moment.minute

    def mark_triggered(self, moment: datetime) -> None:
        self.last_trigger_key = self._trigger_key(moment)
        self.snooze_until = None

    def snooze(self, moment: datetime, minutes: int) -> None:
        if minutes <= 0:
            raise ValueError("Snooze minutes must be greater than zero.")
        self.enabled = True
        self.snooze_until = moment + timedelta(minutes=minutes)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.snooze_until = None

    def status_detail(self) -> str:
        if self.snooze_until is not None:
            return f"postergada hasta {self.snooze_until.strftime('%H:%M')}"
        return f"programada para {self.formatted_time()}"

    def _trigger_key(self, moment: datetime) -> str:
        return moment.strftime("%Y-%m-%d %H:%M")
