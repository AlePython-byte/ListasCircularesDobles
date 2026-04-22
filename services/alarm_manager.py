from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Tuple

from models.alarm import Alarm
from services.sound_service import SoundService


class AlarmManager:
    """Stores alarms and coordinates validation, trigger checks, and actions."""

    def __init__(self) -> None:
        self._alarms: Dict[int, Alarm] = {}
        self._next_id = 1

    def create_alarm(self, hour: int, minute: int, label: str = "") -> Alarm:
        alarm = Alarm(
            alarm_id=self._next_id,
            hour=hour,
            minute=minute,
            label=label.strip(),
            enabled=True,
        )
        self._alarms[alarm.alarm_id] = alarm
        self._next_id += 1
        return alarm

    def get_alarms(self) -> Tuple[Alarm, ...]:
        return tuple(sorted(self._alarms.values(), key=lambda alarm: alarm.alarm_id))

    def get_alarm(self, alarm_id: int) -> Optional[Alarm]:
        return self._alarms.get(alarm_id)

    def enable_alarm(self, alarm_id: int) -> None:
        self._require_alarm(alarm_id).set_enabled(True)

    def disable_alarm(self, alarm_id: int) -> None:
        self._require_alarm(alarm_id).set_enabled(False)

    def delete_alarm(self, alarm_id: int) -> None:
        if alarm_id not in self._alarms:
            raise ValueError("Alarm does not exist.")
        del self._alarms[alarm_id]

    def snooze_alarm(self, alarm_id: int, minutes: int, moment: datetime) -> None:
        self._require_alarm(alarm_id).snooze(moment, minutes)

    def check_alarms(self, moment: datetime) -> Tuple[Alarm, ...]:
        triggered_alarms = []

        for alarm in self._alarms.values():
            if alarm.should_trigger(moment):
                alarm.mark_triggered(moment)
                triggered_alarms.append(alarm)

        return tuple(triggered_alarms)

    def summary_text(self) -> str:
        count = len(self._alarms)
        if count == 0:
            return "No hay alarmas programadas."
        if count == 1:
            return "1 alarma programada."
        return f"{count} alarmas programadas."

    def play_notification_sound(self) -> None:
        SoundService().play_notification_sound()

    def _require_alarm(self, alarm_id: int) -> Alarm:
        alarm = self.get_alarm(alarm_id)
        if alarm is None:
            raise ValueError("Alarm does not exist.")
        return alarm
