from dataclasses import dataclass


@dataclass(frozen=True)
class ClockMarker:
    """Major hour marker placed on the analog clock face."""

    hour: int
    label: str
    angle_degrees: float
