from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Tuple


class ControlPanel(ttk.Frame):
    """Side panel for alarm controls and marker traversal."""

    def __init__(
        self,
        master: tk.Misc,
        on_set_alarm: Callable[[int, int], None],
        on_enable_alarm: Callable[[], None],
        on_disable_alarm: Callable[[], None],
        on_previous_marker: Callable[[], None],
        on_next_marker: Callable[[], None],
        on_current_marker: Callable[[], None],
        on_clear_notice: Callable[[], None],
    ) -> None:
        super().__init__(master, padding=18)
        self._on_set_alarm = on_set_alarm
        self._on_enable_alarm = on_enable_alarm
        self._on_disable_alarm = on_disable_alarm
        self._on_previous_marker = on_previous_marker
        self._on_next_marker = on_next_marker
        self._on_current_marker = on_current_marker
        self._on_clear_notice = on_clear_notice

        self._hour_var = tk.StringVar(value="07")
        self._minute_var = tk.StringVar(value="00")
        self._alarm_status_var = tk.StringVar(value="Alarma: sin configurar")
        self._marker_status_var = tk.StringVar(value="Marcador: 12")
        self._message_var = tk.StringVar(value="Listo")

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
        self._marker_status_var.set(f"Marcador: {hour}")

    def set_message(self, text: str) -> None:
        self._message_var.set(text)

    def show_alarm_notice(self, alarm_time: str) -> None:
        self._message_var.set(f"Alarma sonando: {alarm_time}")
        self._notice_frame.grid()

    def hide_alarm_notice(self) -> None:
        self._notice_frame.grid_remove()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)

        title = ttk.Label(
            self,
            text="Reloj analogico",
            font=("Segoe UI", 18, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 12))

        alarm_frame = ttk.LabelFrame(self, text="Alarma", padding=12)
        alarm_frame.grid(row=1, column=0, sticky="ew", pady=(0, 14))
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
        hour_spinbox.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(3, 10))

        minute_spinbox = ttk.Spinbox(
            alarm_frame,
            from_=0,
            to=59,
            textvariable=self._minute_var,
            width=6,
            format="%02.0f",
        )
        minute_spinbox.grid(row=1, column=1, sticky="ew", pady=(3, 10))

        save_button = ttk.Button(
            alarm_frame,
            text="Guardar alarma",
            command=self._handle_set_alarm,
        )
        save_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))

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
            wraplength=220,
        )
        alarm_status.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        marker_frame = ttk.LabelFrame(self, text="Marcadores", padding=12)
        marker_frame.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        marker_frame.columnconfigure((0, 1), weight=1)

        marker_status = ttk.Label(
            marker_frame,
            textvariable=self._marker_status_var,
            font=("Segoe UI", 11, "bold"),
        )
        marker_status.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

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
        current_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        status_frame = ttk.LabelFrame(self, text="Estado", padding=12)
        status_frame.grid(row=3, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        message_label = ttk.Label(
            status_frame,
            textvariable=self._message_var,
            wraplength=220,
        )
        message_label.grid(row=0, column=0, sticky="w")

        self._notice_frame = ttk.Frame(status_frame)
        self._notice_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self._notice_frame.columnconfigure(0, weight=1)

        notice_label = ttk.Label(
            self._notice_frame,
            text="Aviso visual activo",
            foreground="#c62828",
            font=("Segoe UI", 10, "bold"),
        )
        notice_label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        clear_button = ttk.Button(
            self._notice_frame,
            text="Cerrar aviso",
            command=self._on_clear_notice,
        )
        clear_button.grid(row=1, column=0, sticky="ew")
        self._notice_frame.grid_remove()

    def _handle_set_alarm(self) -> None:
        try:
            hour, minute = self.get_alarm_values()
        except ValueError as error:
            self.set_message(str(error))
            return

        self._on_set_alarm(hour, minute)
