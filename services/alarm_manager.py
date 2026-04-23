from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time as datetime_time
from typing import Dict, Iterable, Optional, Tuple

from models.alarm import Alarm, AlarmScheduleType
from services.sound_service import SoundService


@dataclass(frozen=True)
class AlarmSchedule:
    """Effective next trigger information for one active alarm."""

    alarm: Alarm
    trigger_datetime: datetime
    is_snoozed: bool

    def seconds_until(self, moment: datetime) -> float:
        return max(0.0, (self.trigger_datetime - moment).total_seconds())


class AlarmManager:
    """Stores alarms and coordinates validation, trigger checks, and actions."""

    def __init__(self) -> None:
        self._alarms: Dict[int, Alarm] = {}
        self._next_id = 1

    def create_alarm(
        self,
        hour: int,
        minute: int,
        label: str = "",
        schedule_type: AlarmScheduleType | str = AlarmScheduleType.DAILY,
        weekly_days: Iterable[int] = (),
        target_date: date | str | None = None,
        reference_moment: datetime | None = None,
    ) -> Alarm:
        normalized_label = self._validate_alarm_data(hour, minute, label)
        alarm = Alarm(
            alarm_id=self._next_id,
            hour=hour,
            minute=minute,
            label=normalized_label,
            enabled=True,
            schedule_type=schedule_type,
            weekly_days=weekly_days,
            target_date=target_date,
        )
        self._validate_schedule_data(alarm, reference_moment)
        self._ensure_unique_alarm(alarm)
        self._alarms[alarm.alarm_id] = alarm
        self._next_id += 1
        return alarm

    def update_alarm(
        self,
        alarm_id: int,
        hour: int,
        minute: int,
        label: str = "",
        schedule_type: AlarmScheduleType | str | None = None,
        weekly_days: Iterable[int] = (),
        target_date: date | str | None = None,
        reference_moment: datetime | None = None,
    ) -> Alarm:
        alarm = self._require_alarm(alarm_id)
        normalized_label = self._validate_alarm_data(hour, minute, label)
        next_schedule_type = alarm.schedule_type if schedule_type is None else schedule_type
        next_weekly_days = alarm.weekly_days if schedule_type is None else weekly_days
        next_target_date = alarm.target_date if schedule_type is None else target_date
        candidate = Alarm(
            alarm_id=alarm_id,
            hour=hour,
            minute=minute,
            label=normalized_label,
            enabled=alarm.enabled,
            last_trigger_key=alarm.last_trigger_key,
            snooze_until=alarm.snooze_until,
            schedule_type=next_schedule_type,
            weekly_days=next_weekly_days,
            target_date=next_target_date,
        )
        self._validate_schedule_data(candidate, reference_moment)
        self._ensure_unique_alarm(candidate, excluded_alarm_id=alarm_id)
        alarm.update_schedule(hour, minute, normalized_label)
        if schedule_type is not None:
            alarm.set_schedule_rule(schedule_type, weekly_days, target_date)
        return alarm

    def load_alarms(self, alarms: Iterable[Alarm]) -> None:
        self._alarms = {}
        max_id = 0

        for alarm in alarms:
            if alarm.alarm_id in self._alarms:
                continue
            try:
                self._ensure_unique_alarm(alarm)
            except ValueError:
                continue
            self._alarms[alarm.alarm_id] = alarm
            max_id = max(max_id, alarm.alarm_id)

        self._next_id = max_id + 1

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

    def next_active_alarm(self, moment: Optional[datetime] = None) -> Optional[Alarm]:
        if moment is None:
            active_alarms = [alarm for alarm in self._alarms.values() if alarm.enabled]
            if not active_alarms:
                return None
            return min(active_alarms, key=lambda alarm: (alarm.hour, alarm.minute, alarm.alarm_id))

        next_schedule = self.next_alarm_schedule(moment)
        if next_schedule is None:
            return None
        return next_schedule.alarm

    def next_alarm_schedule(self, moment: datetime) -> Optional[AlarmSchedule]:
        schedules = self.get_effective_schedules(moment)
        if not schedules:
            return None
        return min(
            schedules,
            key=lambda schedule: (
                schedule.seconds_until(moment),
                schedule.trigger_datetime,
                schedule.alarm.alarm_id,
            ),
        )

    def get_effective_schedules(self, moment: datetime) -> Tuple[AlarmSchedule, ...]:
        schedules = []

        for alarm in self._alarms.values():
            trigger_datetime = alarm.effective_trigger_datetime(moment)
            if trigger_datetime is None:
                continue
            schedules.append(
                AlarmSchedule(
                    alarm=alarm,
                    trigger_datetime=trigger_datetime,
                    is_snoozed=alarm.is_snoozed(),
                )
            )

        return tuple(schedules)

    def play_notification_sound(self) -> None:
        SoundService().play_notification_sound()

    def _require_alarm(self, alarm_id: int) -> Alarm:
        alarm = self.get_alarm(alarm_id)
        if alarm is None:
            raise ValueError("Alarm does not exist.")
        return alarm

    def _validate_alarm_data(self, hour: int, minute: int, label: str) -> str:
        if not 0 <= hour <= 23:
            raise ValueError("La hora debe estar entre 0 y 23.")
        if not 0 <= minute <= 59:
            raise ValueError("El minuto debe estar entre 0 y 59.")

        try:
            return Alarm.normalize_label(label)
        except ValueError:
            raise ValueError(
                f"La etiqueta debe tener maximo {Alarm.MAX_LABEL_LENGTH} caracteres."
            ) from None

    def _ensure_unique_alarm(
        self,
        candidate: Alarm,
        excluded_alarm_id: Optional[int] = None,
    ) -> None:
        for alarm in self._alarms.values():
            if alarm.alarm_id == excluded_alarm_id:
                continue
            if alarm.has_same_definition(candidate):
                raise ValueError("Ya existe una alarma con la misma hora y etiqueta.")

    def _validate_schedule_data(
        self,
        alarm: Alarm,
        reference_moment: datetime | None,
    ) -> None:
        if alarm.schedule_type == AlarmScheduleType.WEEKLY and not alarm.weekly_days:
            raise ValueError("Seleccione al menos un dia de la semana.")

        if alarm.schedule_type != AlarmScheduleType.SPECIFIC_DATE:
            return

        if alarm.target_date is None:
            raise ValueError("Seleccione una fecha especifica valida.")

        if reference_moment is None:
            return

        current_minute = reference_moment.replace(second=0, microsecond=0)
        scheduled_datetime = datetime.combine(
            alarm.target_date,
            datetime_time(hour=alarm.hour, minute=alarm.minute),
            tzinfo=reference_moment.tzinfo,
        )
        if scheduled_datetime < current_minute:
            raise ValueError(
                "La fecha y hora especificas ya pasaron en la zona seleccionada."
            )
