from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from models.countdown_timer import CountdownTimer
from ui.numeric_validation import NumericFieldValidator


class CountdownTimerPanel(ttk.Frame):
    """Notebook tab that displays and controls a visual countdown timer."""

    def __init__(self, master: tk.Misc, on_finished: Callable[[], None]) -> None:
        super().__init__(master, padding=16)
        self._timer = CountdownTimer()
        self._on_finished = on_finished
        self._validator = NumericFieldValidator(self)
        self._hours_var = tk.StringVar(value="00")
        self._minutes_var = tk.StringVar(value="05")
        self._seconds_var = tk.StringVar(value="00")
        self._time_var = tk.StringVar(value="00:00:00")
        self._status_var = tk.StringVar(value="Configure una duracion.")
        self._start_button: ttk.Button | None = None
        self._pause_button: ttk.Button | None = None
        self._resume_button: ttk.Button | None = None
        self._reset_button: ttk.Button | None = None
        self._build_layout()
        self._bind_validation()
        self._update_button_states()
        self._update_display()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)

        ttk.Label(
            self,
            text="Temporizador",
            font=("Segoe UI", 15, "bold"),
            anchor=tk.CENTER,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))

        input_frame = ttk.LabelFrame(self, text="Duracion", padding=10)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        input_frame.columnconfigure((0, 1, 2), weight=1)

        validation_command = self._validator.create_range_command(0, 999, 3)
        minute_second_command = self._validator.create_range_command(0, 59, 2)

        self._create_time_field(
            input_frame,
            label="Horas",
            variable=self._hours_var,
            column=0,
            to_value=999,
            validation_command=validation_command,
        )
        self._create_time_field(
            input_frame,
            label="Minutos",
            variable=self._minutes_var,
            column=1,
            to_value=59,
            validation_command=minute_second_command,
        )
        self._create_time_field(
            input_frame,
            label="Segundos",
            variable=self._seconds_var,
            column=2,
            to_value=59,
            validation_command=minute_second_command,
        )

        self._progress_canvas = tk.Canvas(
            self,
            width=190,
            height=190,
            bg="#eef2f3",
            highlightthickness=0,
        )
        self._progress_canvas.grid(row=2, column=0, pady=(0, 10))

        ttk.Label(
            self,
            textvariable=self._time_var,
            font=("Segoe UI", 30, "bold"),
            anchor=tk.CENTER,
        ).grid(row=3, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(
            self,
            textvariable=self._status_var,
            anchor=tk.CENTER,
        ).grid(row=4, column=0, sticky="ew", pady=(0, 14))

        button_frame = ttk.Frame(self)
        button_frame.grid(row=5, column=0, sticky="ew")
        button_frame.columnconfigure((0, 1), weight=1)

        self._start_button = ttk.Button(button_frame, text="Iniciar", command=self._start)
        self._start_button.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))

        self._pause_button = ttk.Button(button_frame, text="Pausar", command=self._pause)
        self._pause_button.grid(row=0, column=1, sticky="ew", pady=(0, 8))

        self._resume_button = ttk.Button(button_frame, text="Reanudar", command=self._resume)
        self._resume_button.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        self._reset_button = ttk.Button(button_frame, text="Reiniciar", command=self._reset)
        self._reset_button.grid(row=1, column=1, sticky="ew")

    def _create_time_field(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        column: int,
        to_value: int,
        validation_command: str,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=0, column=column, sticky="w")
        spinbox = ttk.Spinbox(
            parent,
            from_=0,
            to=to_value,
            textvariable=variable,
            width=7,
            validate="key",
            validatecommand=(validation_command, "%P"),
        )
        spinbox.grid(row=1, column=column, sticky="ew", padx=(0, 8), pady=(3, 0))
        self._validator.attach_focus_normalizer(
            spinbox,
            variable,
            0,
            to_value,
            self._status_var.set,
            allow_empty_as_zero=True,
        )

    def _bind_validation(self) -> None:
        for variable in (self._hours_var, self._minutes_var, self._seconds_var):
            variable.trace_add("write", lambda *_args: self._update_button_states())

    def _start(self) -> None:
        try:
            hours, minutes, seconds = self._read_duration_values(normalize=True)
            self._timer.set_duration(hours, minutes, seconds)
            self._timer.start()
        except ValueError as error:
            self._status_var.set(str(error))
            self._update_button_states()
            return

        self._status_var.set("Temporizador en marcha.")
        self._update_button_states()

    def _pause(self) -> None:
        self._timer.pause()
        self._status_var.set("Temporizador pausado.")
        self._update_button_states()

    def _resume(self) -> None:
        self._timer.resume()
        self._status_var.set("Temporizador en marcha.")
        self._update_button_states()

    def _reset(self) -> None:
        self._timer.reset()
        self._status_var.set("Temporizador reiniciado.")
        self._update_button_states()

    def _update_display(self) -> None:
        self._time_var.set(self._timer.formatted_time())
        self._draw_progress(self._timer.progress_fraction())

        if self._timer.consume_finished():
            self._status_var.set("Temporizador finalizado.")
            self._on_finished()
            self._update_button_states()

        self.after(100, self._update_display)

    def _update_button_states(self) -> None:
        state = self._timer.state
        start_enabled = self._is_duration_ready() and state in ("idle", "finished")
        pause_enabled = state == "running"
        resume_enabled = state == "paused"
        reset_enabled = self._timer.duration_seconds > 0 or state in ("running", "paused", "finished")

        self._set_button_state(self._start_button, start_enabled)
        self._set_button_state(self._pause_button, pause_enabled)
        self._set_button_state(self._resume_button, resume_enabled)
        self._set_button_state(self._reset_button, reset_enabled)

    def _is_duration_ready(self) -> bool:
        try:
            hours, minutes, seconds = self._read_duration_values(normalize=False)
        except ValueError:
            return False
        return hours * 3600 + minutes * 60 + seconds > 0

    def _read_duration_values(self, normalize: bool) -> tuple[int, int, int]:
        raw_values = (
            self._hours_var.get(),
            self._minutes_var.get(),
            self._seconds_var.get(),
        )
        parsed_values = []

        for raw_value, max_value, label in zip(
            raw_values,
            (999, 59, 59),
            ("horas", "minutos", "segundos"),
        ):
            stripped_value = raw_value.strip()
            if stripped_value == "":
                value = 0
            elif stripped_value.isdigit():
                value = int(stripped_value)
            else:
                raise ValueError("Solo se permiten numeros.")

            if not 0 <= value <= max_value:
                raise ValueError(f"El campo {label} debe estar entre 0 y {max_value}.")
            parsed_values.append(value)

        if sum((parsed_values[0] * 3600, parsed_values[1] * 60, parsed_values[2])) <= 0:
            raise ValueError("La duracion debe ser mayor que cero.")

        if normalize:
            self._hours_var.set(f"{parsed_values[0]:02d}")
            self._minutes_var.set(f"{parsed_values[1]:02d}")
            self._seconds_var.set(f"{parsed_values[2]:02d}")

        return parsed_values[0], parsed_values[1], parsed_values[2]

    def _set_button_state(self, button: ttk.Button | None, enabled: bool) -> None:
        if button is not None:
            button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def _draw_progress(self, fraction: float) -> None:
        self._progress_canvas.delete("all")
        pad = 15
        size = 190
        remaining_extent = max(0.0, 1.0 - fraction) * 360
        self._progress_canvas.create_oval(
            pad,
            pad,
            size - pad,
            size - pad,
            outline="#c6d2cf",
            width=12,
        )
        self._progress_canvas.create_arc(
            pad,
            pad,
            size - pad,
            size - pad,
            start=90,
            extent=-remaining_extent,
            style=tk.ARC,
            outline="#d1495b",
            width=12,
        )
        self._progress_canvas.create_text(
            size / 2,
            size / 2,
            text="Restante",
            fill="#263238",
            font=("Segoe UI", 11, "bold"),
        )
