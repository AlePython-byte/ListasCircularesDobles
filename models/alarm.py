from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


@dataclass
class Alarm:
    """Alarm value object with validation, trigger, and snooze behavior."""

    alarm_id: int
    hour: int
    minute: int
    label: str = ""
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

    def display_label(self) -> str:
        return self.label.strip() or "Sin etiqueta"

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alarm_id": self.alarm_id,
            "hour": self.hour,
            "minute": self.minute,
            "label": self.label,
            "enabled": self.enabled,
            "last_trigger_key": self.last_trigger_key,
            "snooze_until": self.snooze_until.isoformat() if self.snooze_until else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alarm":
        snooze_until = data.get("snooze_until")
        parsed_snooze = None
        if isinstance(snooze_until, str) and snooze_until:
            try:
                parsed_snooze = datetime.fromisoformat(snooze_until)
            except ValueError:
                parsed_snooze = None
            if parsed_snooze is not None and parsed_snooze.tzinfo is None:
                parsed_snooze = None

        return cls(
            alarm_id=int(data["alarm_id"]),
            hour=int(data["hour"]),
            minute=int(data["minute"]),
            label=str(data.get("label", "")),
            enabled=bool(data.get("enabled", True)),
            last_trigger_key=data.get("last_trigger_key"),
            snooze_until=parsed_snooze,
        )

    def _trigger_key(self, moment: datetime) -> str:
        return moment.strftime("%Y-%m-%d %H:%M")
