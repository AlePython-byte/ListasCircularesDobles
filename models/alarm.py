from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time as datetime_time, timedelta
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Tuple


class AlarmScheduleType(str, Enum):
    """Supported recurrence rules for alarms."""

    DAILY = "daily"
    WEEKLY = "weekly"
    SPECIFIC_DATE = "specific_date"


@dataclass
class Alarm:
    """Alarm value object with validation, trigger, and snooze behavior."""

    MAX_LABEL_LENGTH = 40

    alarm_id: int
    hour: int
    minute: int
    label: str = ""
    enabled: bool = True
    last_trigger_key: Optional[str] = None
    snooze_until: Optional[datetime] = None
    schedule_type: AlarmScheduleType = AlarmScheduleType.DAILY
    weekly_days: Tuple[int, ...] = ()
    target_date: Optional[date] = None

    def __post_init__(self) -> None:
        if self.alarm_id <= 0:
            raise ValueError("Alarm id must be greater than zero.")
        self._validate_time(self.hour, self.minute)
        self.label = self.normalize_label(self.label)
        self.last_trigger_key = self._normalize_trigger_key(self.last_trigger_key)
        if self.snooze_until is not None and self.snooze_until.tzinfo is None:
            self.snooze_until = None
        self._normalize_schedule_fields()

    def update_schedule(self, hour: int, minute: int, label: str) -> None:
        self._validate_time(hour, minute)
        self.hour = hour
        self.minute = minute
        self.label = self.normalize_label(label)
        self.last_trigger_key = None
        self.clear_snooze()

    def set_schedule_rule(
        self,
        schedule_type: AlarmScheduleType | str,
        weekly_days: Iterable[int] = (),
        target_date: date | str | None = None,
    ) -> None:
        """Update the recurrence rule while preserving the base time."""
        self.schedule_type = self._parse_schedule_type(schedule_type)
        self.weekly_days = self._parse_weekly_days(weekly_days)
        self.target_date = self._parse_target_date(target_date)
        self._normalize_schedule_fields()
        self.last_trigger_key = None
        self.clear_snooze()

    def _validate_time(self, hour: int, minute: int) -> None:
        if not 0 <= hour <= 23:
            raise ValueError("Hour must be between 0 and 23.")
        if not 0 <= minute <= 59:
            raise ValueError("Minute must be between 0 and 59.")

    def formatted_time(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def display_label(self) -> str:
        return self.label or "Sin etiqueta"

    def is_snoozed(self) -> bool:
        return self.enabled and self.snooze_until is not None

    def is_waiting_for_base_time(self) -> bool:
        return self.enabled and self.snooze_until is None

    def should_trigger(self, moment: datetime) -> bool:
        if not self.enabled:
            return False

        if self.was_triggered_during(moment):
            return False

        if self.is_snoozed():
            return self.is_snooze_due(moment)

        return self.is_scheduled_for(moment)

    def mark_triggered(self, moment: datetime) -> None:
        self.last_trigger_key = self._trigger_key(moment)
        self.clear_snooze()

    def snooze(self, moment: datetime, minutes: int) -> None:
        if minutes <= 0:
            raise ValueError("Snooze minutes must be greater than zero.")
        self.enabled = True
        self.snooze_until = moment + timedelta(minutes=minutes)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.clear_snooze()

    def clear_snooze(self) -> None:
        self.snooze_until = None

    def was_triggered_during(self, moment: datetime) -> bool:
        return self.last_trigger_key == self._trigger_key(moment)

    def is_snooze_due(self, moment: datetime) -> bool:
        return self.snooze_until is not None and moment >= self.snooze_until

    def is_scheduled_for(self, moment: datetime) -> bool:
        if self.hour != moment.hour or self.minute != moment.minute:
            return False

        if self.schedule_type == AlarmScheduleType.DAILY:
            return True
        if self.schedule_type == AlarmScheduleType.WEEKLY:
            return moment.weekday() in self.weekly_days
        if self.schedule_type == AlarmScheduleType.SPECIFIC_DATE:
            return self.target_date == moment.date()
        return False

    def effective_trigger_datetime(self, moment: datetime) -> Optional[datetime]:
        """Return the next datetime this alarm can trigger from the given moment."""
        if not self.enabled:
            return None

        if self.is_snoozed():
            if self.snooze_until is not None and self.snooze_until > moment:
                return self.snooze_until
            return moment

        if self.schedule_type == AlarmScheduleType.DAILY:
            return self._next_daily_trigger_datetime(moment)
        if self.schedule_type == AlarmScheduleType.WEEKLY:
            return self._next_weekly_trigger_datetime(moment)
        if self.schedule_type == AlarmScheduleType.SPECIFIC_DATE:
            return self._next_specific_date_trigger_datetime(moment)
        return None

    def next_trigger_datetime(self, moment: datetime) -> Optional[datetime]:
        return self.effective_trigger_datetime(moment)

    def has_same_definition(self, other: "Alarm") -> bool:
        return (
            self.hour == other.hour
            and self.minute == other.minute
            and self.label == other.label
            and self.schedule_type == other.schedule_type
            and self.weekly_days == other.weekly_days
            and self.target_date == other.target_date
        )

    def status_detail(self) -> str:
        if self.snooze_until is not None:
            return f"postergada hasta {self.snooze_until.strftime('%H:%M')}"
        if self.schedule_type == AlarmScheduleType.WEEKLY:
            return f"programada semanalmente para {self.formatted_time()}"
        if self.schedule_type == AlarmScheduleType.SPECIFIC_DATE and self.target_date:
            return f"programada para {self.target_date.isoformat()} {self.formatted_time()}"
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
            "schedule_type": self.schedule_type.value,
            "weekly_days": list(self.weekly_days),
            "target_date": self.target_date.isoformat() if self.target_date else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alarm":
        return cls(
            alarm_id=int(data["alarm_id"]),
            hour=int(data["hour"]),
            minute=int(data["minute"]),
            label=cls._parse_label(data.get("label", "")),
            enabled=cls._parse_enabled(data.get("enabled", True)),
            last_trigger_key=cls._normalize_trigger_key(data.get("last_trigger_key")),
            snooze_until=cls._parse_snooze_until(data.get("snooze_until")),
            schedule_type=cls._parse_schedule_type(data.get("schedule_type")),
            weekly_days=cls._parse_weekly_days(data.get("weekly_days", ())),
            target_date=cls._parse_target_date(data.get("target_date")),
        )

    def _trigger_key(self, moment: datetime) -> str:
        return moment.strftime("%Y-%m-%d %H:%M")

    def _normalize_schedule_fields(self) -> None:
        self.schedule_type = self._parse_schedule_type(self.schedule_type)
        self.weekly_days = self._parse_weekly_days(self.weekly_days)
        self.target_date = self._parse_target_date(self.target_date)

        if self.schedule_type != AlarmScheduleType.WEEKLY:
            self.weekly_days = ()
        if self.schedule_type != AlarmScheduleType.SPECIFIC_DATE:
            self.target_date = None

    def _next_daily_trigger_datetime(self, moment: datetime) -> datetime:
        scheduled_time = self._datetime_on_date(moment, moment.date())
        if scheduled_time <= moment:
            scheduled_time += timedelta(days=1)
        return scheduled_time

    def _next_weekly_trigger_datetime(self, moment: datetime) -> Optional[datetime]:
        if not self.weekly_days:
            return None

        for days_ahead in range(8):
            candidate_date = moment.date() + timedelta(days=days_ahead)
            if candidate_date.weekday() not in self.weekly_days:
                continue

            candidate = self._datetime_on_date(moment, candidate_date)
            if candidate > moment:
                return candidate
        return None

    def _next_specific_date_trigger_datetime(self, moment: datetime) -> Optional[datetime]:
        if self.target_date is None:
            return None

        scheduled_time = self._datetime_on_date(moment, self.target_date)
        if scheduled_time <= moment:
            return None
        return scheduled_time

    def _datetime_on_date(self, moment: datetime, target_day: date) -> datetime:
        return datetime.combine(
            target_day,
            datetime_time(hour=self.hour, minute=self.minute),
            tzinfo=moment.tzinfo,
        )

    @staticmethod
    def _parse_label(value: Any) -> str:
        if value is None:
            return ""
        normalized = " ".join(str(value).split())
        return normalized[: Alarm.MAX_LABEL_LENGTH]

    @classmethod
    def normalize_label(cls, value: Any) -> str:
        raw_text = str(value).strip()
        if not all(character.isprintable() for character in raw_text):
            raise ValueError("Label contains invalid characters.")

        normalized = " ".join(raw_text.split())
        if len(normalized) > cls.MAX_LABEL_LENGTH:
            raise ValueError("Label is too long.")
        return normalized

    @staticmethod
    def _parse_enabled(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        raise ValueError("Enabled state must be a boolean value.")

    @staticmethod
    def _parse_snooze_until(value: Any) -> Optional[datetime]:
        if not isinstance(value, str) or not value:
            return None

        try:
            parsed_value = datetime.fromisoformat(value)
        except ValueError:
            return None

        if parsed_value.tzinfo is None:
            return None
        return parsed_value

    @staticmethod
    def _parse_schedule_type(value: Any) -> AlarmScheduleType:
        if isinstance(value, AlarmScheduleType):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            for schedule_type in AlarmScheduleType:
                if normalized == schedule_type.value:
                    return schedule_type

        return AlarmScheduleType.DAILY

    @staticmethod
    def _parse_weekly_days(value: Any) -> Tuple[int, ...]:
        if value is None or isinstance(value, (str, bytes)):
            return ()

        try:
            values = tuple(value)
        except TypeError:
            return ()

        normalized_days = set()
        for item in values:
            try:
                weekday = int(item)
            except (TypeError, ValueError):
                continue
            if 0 <= weekday <= 6:
                normalized_days.add(weekday)
        return tuple(sorted(normalized_days))

    @staticmethod
    def _parse_target_date(value: Any) -> Optional[date]:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if not isinstance(value, str) or not value:
            return None

        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _normalize_trigger_key(value: Any) -> Optional[str]:
        if not isinstance(value, str) or not value.strip():
            return None

        normalized = value.strip()
        try:
            datetime.strptime(normalized, "%Y-%m-%d %H:%M")
        except ValueError:
            return None
        return normalized
