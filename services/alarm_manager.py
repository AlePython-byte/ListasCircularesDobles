from __future__ import annotations

from datetime import datetime
from typing import Optional

from models.alarm import Alarm


class AlarmManager:
    """Coordinates alarm state, validation, and trigger checks."""

    def __init__(self) -> None:
        self._alarm: Optional[Alarm] = None

    @property
    def alarm(self) -> Optional[Alarm]:
        return self._alarm

    def set_alarm(self, hour: int, minute: int) -> Alarm:
        self._alarm = Alarm(hour=hour, minute=minute, enabled=True)
        return self._alarm

    def enable_alarm(self) -> None:
        if self._alarm is None:
            raise ValueError("No alarm has been configured.")
        self._alarm.set_enabled(True)

    def disable_alarm(self) -> None:
        if self._alarm is None:
            raise ValueError("No alarm has been configured.")
        self._alarm.set_enabled(False)

    def check_alarm(self, moment: datetime) -> bool:
        if self._alarm is None:
            return False

        if self._alarm.should_trigger(moment):
            self._alarm.mark_triggered(moment)
            self.play_notification_sound()
            return True

        return False

    def status_text(self) -> str:
        if self._alarm is None:
            return "Alarma: sin configurar"

        state = "activada" if self._alarm.enabled else "desactivada"
        return f"Alarma {state}: {self._alarm.formatted_time()}"

    def play_notification_sound(self) -> None:
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            print("\a", end="")
