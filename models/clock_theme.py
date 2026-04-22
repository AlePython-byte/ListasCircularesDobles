from dataclasses import dataclass


@dataclass(frozen=True)
class ClockTheme:
    """Visual theme used by the analog clock canvas."""

    key: str
    display_name: str
    background_color: str
    face_color: str
    border_color: str
    inner_border_color: str
    hour_hand_color: str
    minute_hand_color: str
    second_hand_color: str
    marker_color: str
    tick_color: str
    minor_tick_color: str
    center_color: str
    alarm_color: str
