from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo
from typing import Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from models.world_clock import WorldClockEntry, WorldTimeSnapshot


class WorldTimeService:
    """Creates live time snapshots for configured world cities."""

    def __init__(self) -> None:
        self._entries = (
            WorldClockEntry(
                city="Bogot\u00e1",
                country="Colombia",
                zone_name="America/Bogota",
                fallback_timezone=timezone(timedelta(hours=-5), "UTC-05:00"),
            ),
            WorldClockEntry(
                city="Nueva York",
                country="Estados Unidos",
                zone_name="America/New_York",
                fallback_timezone=timezone(timedelta(hours=-5), "UTC-05:00"),
            ),
            WorldClockEntry(
                city="Londres",
                country="Reino Unido",
                zone_name="Europe/London",
                fallback_timezone=timezone.utc,
            ),
            WorldClockEntry(
                city="Tokio",
                country="Japon",
                zone_name="Asia/Tokyo",
                fallback_timezone=timezone(timedelta(hours=9), "UTC+09:00"),
            ),
        )

    def get_entries(self) -> Tuple[WorldClockEntry, ...]:
        return self._entries

    def find_entry(self, city: str) -> WorldClockEntry:
        for entry in self._entries:
            if entry.city == city or (city == "Bogota" and entry.zone_name == "America/Bogota"):
                return entry
        raise LookupError("World clock entry was not found.")

    def get_time_for_entry(self, moment: datetime, entry: WorldClockEntry) -> datetime:
        return moment.astimezone(self.get_timezone(entry))

    def get_snapshots(self, moment: datetime) -> Tuple[WorldTimeSnapshot, ...]:
        snapshots = []

        for entry in self._entries:
            local_time = self.get_time_for_entry(moment, entry)
            snapshots.append(
                WorldTimeSnapshot(
                    city=entry.city,
                    country=entry.country,
                    time_text=local_time.strftime("%H:%M:%S"),
                    date_text=local_time.strftime("%d/%m/%Y"),
                    zone_text=local_time.tzname() or entry.zone_name,
                )
            )

        return tuple(snapshots)

    def get_timezone(self, entry: WorldClockEntry) -> tzinfo:
        try:
            return ZoneInfo(entry.zone_name)
        except ZoneInfoNotFoundError:
            return entry.fallback_timezone
