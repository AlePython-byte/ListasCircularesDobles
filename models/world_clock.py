from dataclasses import dataclass
from datetime import tzinfo


@dataclass(frozen=True)
class WorldClockEntry:
    """Configured world clock location."""

    city: str
    country: str
    zone_name: str
    fallback_timezone: tzinfo


@dataclass(frozen=True)
class WorldTimeSnapshot:
    """Rendered time information for one world clock location."""

    city: str
    country: str
    time_text: str
    date_text: str
    zone_text: str
