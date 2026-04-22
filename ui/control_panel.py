from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Iterable, Tuple

from models.clock_theme import ClockTheme
from models.world_clock import WorldTimeSnapshot


class ControlPanel(ttk.Frame):
    """Side panel for alarm, world time, theme, and marker controls."""

    def __init__(
        self,
        master: tk.Misc,
        themes: Iterable[ClockTheme],
        on_set_alarm: Callable[[int, int], None],
        on_enable_alarm: Callable[[], None],
        on_disable_alarm: Callable[[], None],
        on_theme_change: Callable[[str], None],
        on_previous_marker: Callable[[], None],
        on_next_marker: Callable[[], None],
        on_current_marker: Callable[[], None],
    ) -> None:
        super().__init__(master, padding=16)
        self._themes = tuple(themes)
        self._on_set_alarm = on_set_alarm
        self._on_enable_alarm = on_enable_alarm
        self._on_disable_alarm = on_disable_alarm
        self._on_theme_change = on_theme_change
        self._on_previous_marker = on_previous_marker
        self._on_next_marker = on_next_marker
        self._on_current_marker = on_current_marker

        self._hour_var = tk.StringVar(value="07")
        self._minute_var = tk.StringVar(value="00")
        self._alarm_status_var = tk.StringVar(value="Alarma: sin configurar")
        self._marker_status_var = tk.StringVar(value="Marcador seleccionado: 12")
        self._message_var = tk.StringVar(value="Listo")
        self._theme_var = tk.StringVar(value=self._themes[0].display_name)
        self._world_time_vars: Dict[str, tk.StringVar] = {}

        self._build_layout()

    def get_alarm_values(self) -> Tuple[int, int]:
        try:
            hour = int(self._hour_var.get())
            minute = int(self._minute_var.get())
        except ValueError as exc:
            raise ValueError("Use valores numericos para la alarma.") from exc

        if not 0 <= hour <= 23:
            raise ValueError("La hora debe estar entre 0 y 23.")
        if not 0 <= minute <= 59:
            raise ValueError("El minuto debe estar entre 0 y 59.")

        return hour, minute

    def set_alarm_status(self, text: str) -> None:
        self._alarm_status_var.set(text)

    def set_marker_status(self, hour: int) -> None:
        self._marker_status_var.set(f"Marcador seleccionado: {hour}")

    def set_message(self, text: str) -> None:
        self._message_var.set(text)

    def show_alarm_notice(self, alarm_time: str) -> None:
        self._message_var.set(f"Alarma sonando: {alarm_time}")

    def hide_alarm_notice(self) -> None:
        self._message_var.set("Listo")

    def update_world_times(self, snapshots: Iterable[WorldTimeSnapshot]) -> None:
        for snapshot in snapshots:
            text = (
                f"{snapshot.city}: {snapshot.time_text}\n"
                f"{snapshot.country} | {snapshot.date_text} | {snapshot.zone_text}"
            )
            self._world_time_vars[snapshot.city].set(text)

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)

        title = ttk.Label(
            self,
            text="Reloj analogico",
            font=("Segoe UI", 18, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self._build_alarm_frame(row=1)
        self._build_world_time_frame(row=2)
        self._build_theme_frame(row=3)
        self._build_marker_frame(row=4)
        self._build_status_frame(row=5)

    def _build_alarm_frame(self, row: int) -> None:
        alarm_frame = ttk.LabelFrame(self, text="Alarma", padding=10)
        alarm_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        alarm_frame.columnconfigure((0, 1), weight=1)

        ttk.Label(alarm_frame, text="Hora").grid(row=0, column=0, sticky="w")
        ttk.Label(alarm_frame, text="Minuto").grid(row=0, column=1, sticky="w")

        hour_spinbox = ttk.Spinbox(
            alarm_frame,
            from_=0,
            to=23,
            textvariable=self._hour_var,
            width=6,
            format="%02.0f",
        )
        hour_spinbox.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(3, 8))

        minute_spinbox = ttk.Spinbox(
            alarm_frame,
            from_=0,
            to=59,
            textvariable=self._minute_var,
            width=6,
            format="%02.0f",
        )
        minute_spinbox.grid(row=1, column=1, sticky="ew", pady=(3, 8))

        save_button = ttk.Button(
            alarm_frame,
            text="Guardar alarma",
            command=self._handle_set_alarm,
        )
        save_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 7))

        enable_button = ttk.Button(
            alarm_frame,
            text="Activar",
            command=self._on_enable_alarm,
        )
        enable_button.grid(row=3, column=0, sticky="ew", padx=(0, 8))

        disable_button = ttk.Button(
            alarm_frame,
            text="Desactivar",
            command=self._on_disable_alarm,
        )
        disable_button.grid(row=3, column=1, sticky="ew")

        alarm_status = ttk.Label(
            alarm_frame,
            textvariable=self._alarm_status_var,
            wraplength=245,
        )
        alarm_status.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _build_world_time_frame(self, row: int) -> None:
        world_frame = ttk.LabelFrame(self, text="Horas mundiales", padding=10)
        world_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        world_frame.columnconfigure(0, weight=1)

        for index, city in enumerate(("Nueva York", "Londres", "Tokio")):
            value = tk.StringVar(value=f"{city}: --:--:--")
            self._world_time_vars[city] = value
            label = ttk.Label(
                world_frame,
                textvariable=value,
                font=("Segoe UI", 9),
                wraplength=245,
            )
            label.grid(row=index, column=0, sticky="w", pady=(0, 6))

    def _build_theme_frame(self, row: int) -> None:
        theme_frame = ttk.LabelFrame(self, text="Apariencia", padding=10)
        theme_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        theme_frame.columnconfigure(0, weight=1)

        theme_names = tuple(theme.display_name for theme in self._themes)
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self._theme_var,
            values=theme_names,
            state="readonly",
        )
        theme_combo.grid(row=0, column=0, sticky="ew")
        theme_combo.bind("<<ComboboxSelected>>", self._handle_theme_change)

    def _build_marker_frame(self, row: int) -> None:
        marker_frame = ttk.LabelFrame(self, text="Recorrido circular", padding=10)
        marker_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        marker_frame.columnconfigure((0, 1), weight=1)

        marker_status = ttk.Label(
            marker_frame,
            textvariable=self._marker_status_var,
            font=("Segoe UI", 10, "bold"),
        )
        marker_status.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 7))

        previous_button = ttk.Button(
            marker_frame,
            text="Anterior",
            command=self._on_previous_marker,
        )
        previous_button.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        next_button = ttk.Button(
            marker_frame,
            text="Siguiente",
            command=self._on_next_marker,
        )
        next_button.grid(row=1, column=1, sticky="ew")

        current_button = ttk.Button(
            marker_frame,
            text="Hora actual",
            command=self._on_current_marker,
        )
        current_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(7, 0))

    def _build_status_frame(self, row: int) -> None:
        status_frame = ttk.LabelFrame(self, text="Estado", padding=10)
        status_frame.grid(row=row, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        message_label = ttk.Label(
            status_frame,
            textvariable=self._message_var,
            wraplength=245,
        )
        message_label.grid(row=0, column=0, sticky="w")

    def _handle_set_alarm(self) -> None:
        try:
            hour, minute = self.get_alarm_values()
        except ValueError as error:
            self.set_message(str(error))
            return

        self._on_set_alarm(hour, minute)

    def _handle_theme_change(self, _event: tk.Event) -> None:
        self._on_theme_change(self._theme_var.get())
