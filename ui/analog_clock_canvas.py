from __future__ import annotations

import math
import tkinter as tk
from datetime import datetime
from typing import Dict, Iterable, Optional, Tuple

from models.clock_marker import ClockMarker
from models.clock_theme import ClockTheme


class AnalogClockCanvas(tk.Canvas):
    """Canvas widget that draws an analog clock face and hands."""

    def __init__(self, master: tk.Misc, theme: ClockTheme, **kwargs: object) -> None:
        self._theme = theme
        super().__init__(
            master,
            width=460,
            height=460,
            bg=theme.background_color,
            highlightthickness=0,
            **kwargs,
        )
        self._last_moment: Optional[datetime] = None
        self._last_angles: Optional[Dict[str, float]] = None
        self._last_markers: Optional[Iterable[ClockMarker]] = None
        self._alarm_visible = False
        self._scene_ready = False
        self._last_size: Tuple[int, int] = (0, 0)
        self._hand_items: Dict[str, int] = {}
        self._center_cap_item: Optional[int] = None
        self._alarm_notice_items: list[int] = []
        self.bind("<Configure>", self._handle_resize)

    def set_theme(self, theme: ClockTheme) -> None:
        self._theme = theme
        self.configure(bg=theme.background_color)
        self._invalidate_scene()
        self._render_scene()

    def render(
        self,
        moment: datetime,
        angles: Dict[str, float],
        markers: Iterable[ClockMarker],
        alarm_visible: bool,
    ) -> None:
        marker_tuple = tuple(markers)
        markers_changed = marker_tuple != self._last_markers

        self._last_moment = moment
        self._last_angles = angles
        self._last_markers = marker_tuple
        self._alarm_visible = alarm_visible

        if markers_changed:
            self._invalidate_scene()

        self._render_scene()

    def _handle_resize(self, _event: tk.Event) -> None:
        self._invalidate_scene()
        self._render_scene()

    def _invalidate_scene(self) -> None:
        self._scene_ready = False
        self._hand_items = {}
        self._center_cap_item = None
        self._alarm_notice_items = []

    def _render_scene(self) -> None:
        if self._last_angles is None or self._last_markers is None:
            return

        width = max(self.winfo_width(), 1)
        height = max(self.winfo_height(), 1)
        center = (width / 2, height / 2)
        radius = min(width, height) * 0.42

        if (width, height) != self._last_size:
            self._invalidate_scene()

        if not self._scene_ready:
            self.delete("all")
            self._last_size = (width, height)
            self._draw_static_scene(center, radius)
            self._create_hand_items()
            self._create_center_cap()
            self._scene_ready = True

        self._update_hands(center, radius, self._last_angles)
        self._update_center_cap(center, radius)
        self._update_alarm_notice(center, radius)

    def _draw_static_scene(self, center: Tuple[float, float], radius: float) -> None:
        self._draw_face(center, radius)
        self._draw_minute_ticks(center, radius)
        self._draw_hour_markers(center, radius, self._last_markers or ())

    def _draw_face(self, center: Tuple[float, float], radius: float) -> None:
        x, y = center
        self.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill=self._theme.face_color,
            outline=self._theme.border_color,
            width=4,
        )
        self.create_oval(
            x - radius * 0.95,
            y - radius * 0.95,
            x + radius * 0.95,
            y + radius * 0.95,
            outline=self._theme.inner_border_color,
            width=2,
        )

    def _draw_minute_ticks(self, center: Tuple[float, float], radius: float) -> None:
        for minute in range(60):
            angle = minute * 6.0
            outer = self._point_from_angle(center, radius * 0.92, angle)
            inner_radius = radius * (0.86 if minute % 5 == 0 else 0.89)
            inner = self._point_from_angle(center, inner_radius, angle)
            color = self._theme.tick_color if minute % 5 == 0 else self._theme.minor_tick_color
            width = 2 if minute % 5 == 0 else 1
            self.create_line(inner[0], inner[1], outer[0], outer[1], fill=color, width=width)

    def _draw_hour_markers(
        self,
        center: Tuple[float, float],
        radius: float,
        markers: Iterable[ClockMarker],
    ) -> None:
        for marker in markers:
            text_point = self._point_from_angle(center, radius * 0.72, marker.angle_degrees)

            self.create_text(
                text_point[0],
                text_point[1],
                text=marker.label,
                fill=self._theme.marker_color,
                font=("Segoe UI", 18, "bold"),
            )

    def _draw_hands(
        self,
        center: Tuple[float, float],
        radius: float,
        angles: Dict[str, float],
    ) -> None:
        self._update_hand("hour", center, radius * 0.46, angles["hour"])
        self._update_hand("minute", center, radius * 0.66, angles["minute"])
        self._update_hand("second", center, radius * 0.76, angles["second"])

    def _create_hand_items(self) -> None:
        self._hand_items = {
            "hour": self.create_line(
                0,
                0,
                0,
                0,
                fill=self._theme.hour_hand_color,
                width=8,
                capstyle=tk.ROUND,
            ),
            "minute": self.create_line(
                0,
                0,
                0,
                0,
                fill=self._theme.minute_hand_color,
                width=5,
                capstyle=tk.ROUND,
            ),
            "second": self.create_line(
                0,
                0,
                0,
                0,
                fill=self._theme.second_hand_color,
                width=2,
                capstyle=tk.ROUND,
            ),
        }

    def _update_hands(
        self,
        center: Tuple[float, float],
        radius: float,
        angles: Dict[str, float],
    ) -> None:
        self._draw_hands(center, radius, angles)

    def _update_hand(
        self,
        hand_name: str,
        center: Tuple[float, float],
        length: float,
        angle_degrees: float,
    ) -> None:
        end = self._point_from_angle(center, length, angle_degrees)
        back = self._point_from_angle(center, length * -0.11, angle_degrees)
        self.coords(
            self._hand_items[hand_name],
            back[0],
            back[1],
            end[0],
            end[1],
        )

    def _create_center_cap(self) -> None:
        self._center_cap_item = self.create_oval(
            0,
            0,
            0,
            0,
            fill=self._theme.center_color,
            outline=self._theme.face_color,
            width=2,
        )

    def _update_center_cap(self, center: Tuple[float, float], radius: float) -> None:
        if self._center_cap_item is None:
            return

        x, y = center
        cap_radius = max(radius * 0.035, 6)
        self.coords(
            self._center_cap_item,
            x - cap_radius,
            y - cap_radius,
            x + cap_radius,
            y + cap_radius,
        )
        self.itemconfig(
            self._center_cap_item,
            fill=self._theme.center_color,
            outline=self._theme.face_color,
            width=2,
        )

    def _update_alarm_notice(self, center: Tuple[float, float], radius: float) -> None:
        if self._alarm_visible:
            if not self._alarm_notice_items:
                self._draw_alarm_notice(center, radius)
            else:
                self._position_alarm_notice(center, radius)
            return

        if self._alarm_notice_items:
            for item in self._alarm_notice_items:
                self.delete(item)
            self._alarm_notice_items = []

    def _draw_alarm_notice(self, center: Tuple[float, float], radius: float) -> None:
        x, y = center
        notice_oval = self.create_oval(
            x - radius * 1.04,
            y - radius * 1.04,
            x + radius * 1.04,
            y + radius * 1.04,
            outline=self._theme.alarm_color,
            width=5,
        )
        notice_text = self.create_text(
            x,
            y + radius * 0.43,
            text="ALARMA",
            fill=self._theme.alarm_color,
            font=("Segoe UI", 17, "bold"),
        )
        self._alarm_notice_items = [notice_oval, notice_text]

    def _position_alarm_notice(self, center: Tuple[float, float], radius: float) -> None:
        x, y = center
        notice_oval, notice_text = self._alarm_notice_items
        self.coords(
            notice_oval,
            x - radius * 1.04,
            y - radius * 1.04,
            x + radius * 1.04,
            y + radius * 1.04,
        )
        self.itemconfig(notice_oval, outline=self._theme.alarm_color)
        self.coords(notice_text, x, y + radius * 0.43)
        self.itemconfig(notice_text, fill=self._theme.alarm_color)

    def _point_from_angle(
        self,
        center: Tuple[float, float],
        length: float,
        angle_degrees: float,
    ) -> Tuple[float, float]:
        radians = math.radians(angle_degrees)
        return (
            center[0] + math.sin(radians) * length,
            center[1] - math.cos(radians) * length,
        )
