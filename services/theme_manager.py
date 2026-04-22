from __future__ import annotations

from typing import Tuple

from models.clock_theme import ClockTheme


class ThemeManager:
    """Provides predefined visual themes for the analog clock."""

    def __init__(self) -> None:
        self._themes = (
            ClockTheme(
                key="classic",
                display_name="Clasico",
                background_color="#eef2f3",
                face_color="#fbfaf7",
                border_color="#1f2933",
                inner_border_color="#d5ded9",
                hour_hand_color="#111827",
                minute_hand_color="#263238",
                second_hand_color="#c62828",
                marker_color="#111827",
                tick_color="#25313b",
                minor_tick_color="#9aa8a1",
                selected_marker_color="#2f80ed",
                selected_text_color="#0f4aa1",
                center_color="#111827",
                alarm_color="#c62828",
            ),
            ClockTheme(
                key="dark",
                display_name="Oscuro",
                background_color="#20262e",
                face_color="#111820",
                border_color="#d8dee9",
                inner_border_color="#536170",
                hour_hand_color="#f7fafc",
                minute_hand_color="#cfd8dc",
                second_hand_color="#ff6b6b",
                marker_color="#f4f6f8",
                tick_color="#d8dee9",
                minor_tick_color="#6f7e8c",
                selected_marker_color="#f2c94c",
                selected_text_color="#f2c94c",
                center_color="#f7fafc",
                alarm_color="#ff6b6b",
            ),
            ClockTheme(
                key="blue",
                display_name="Azul",
                background_color="#eaf3fb",
                face_color="#f7fbff",
                border_color="#145ea8",
                inner_border_color="#a7c8e8",
                hour_hand_color="#0b2545",
                minute_hand_color="#144c7d",
                second_hand_color="#e94f37",
                marker_color="#0b2545",
                tick_color="#145ea8",
                minor_tick_color="#8db6d8",
                selected_marker_color="#00a6a6",
                selected_text_color="#006d77",
                center_color="#0b2545",
                alarm_color="#e94f37",
            ),
            ClockTheme(
                key="green",
                display_name="Verde",
                background_color="#edf5ef",
                face_color="#fbfff9",
                border_color="#276749",
                inner_border_color="#a8d5ba",
                hour_hand_color="#173f2a",
                minute_hand_color="#276749",
                second_hand_color="#d1495b",
                marker_color="#173f2a",
                tick_color="#2f855a",
                minor_tick_color="#8bb99d",
                selected_marker_color="#f2c94c",
                selected_text_color="#805b10",
                center_color="#173f2a",
                alarm_color="#d1495b",
            ),
        )

    def get_themes(self) -> Tuple[ClockTheme, ...]:
        return self._themes

    def get_default_theme(self) -> ClockTheme:
        return self._themes[0]

    def find_by_display_name(self, display_name: str) -> ClockTheme:
        for theme in self._themes:
            if theme.display_name == display_name:
                return theme
        raise LookupError("Theme was not found.")
