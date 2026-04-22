from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from models.countdown_timer import CountdownTimer


class CountdownTimerPanel(ttk.Frame):
    """Notebook tab that displays and controls a visual countdown timer."""

    def __init__(self, master: tk.Misc, on_finished: Callable[[], None]) -> None:
        super().__init__(master, padding=16)
        self._timer = CountdownTimer()
        self._on_finished = on_finished
        self._minutes_var = tk.StringVar(value="05")
        self._seconds_var = tk.StringVar(value="00")
        self._time_var = tk.StringVar(value="00:00")
        self._status_var = tk.StringVar(value="Configure una duraci\u00f3n.")
        self._build_layout()
        self._update_display()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)

        title = ttk.Label(
            self,
            text="Temporizador",
            font=("Segoe UI", 15, "bold"),
            anchor=tk.CENTER,
        )
        title.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        input_frame = ttk.LabelFrame(self, text="Duraci\u00f3n", padding=10)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        input_frame.columnconfigure((0, 1), weight=1)

        ttk.Label(input_frame, text="Minutos").grid(row=0, column=0, sticky="w")
        ttk.Label(input_frame, text="Segundos").grid(row=0, column=1, sticky="w")

        ttk.Spinbox(
            input_frame,
            from_=0,
            to=999,
            textvariable=self._minutes_var,
            width=7,
            format="%02.0f",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(3, 0))

        ttk.Spinbox(
            input_frame,
            from_=0,
            to=59,
            textvariable=self._seconds_var,
            width=7,
            format="%02.0f",
        ).grid(row=1, column=1, sticky="ew", pady=(3, 0))

        self._progress_canvas = tk.Canvas(
            self,
            width=190,
            height=190,
            bg="#eef2f3",
            highlightthickness=0,
        )
        self._progress_canvas.grid(row=2, column=0, pady=(0, 10))

        time_label = ttk.Label(
            self,
            textvariable=self._time_var,
            font=("Segoe UI", 32, "bold"),
            anchor=tk.CENTER,
        )
        time_label.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        status_label = ttk.Label(
            self,
            textvariable=self._status_var,
            anchor=tk.CENTER,
        )
        status_label.grid(row=4, column=0, sticky="ew", pady=(0, 14))

        button_frame = ttk.Frame(self)
        button_frame.grid(row=5, column=0, sticky="ew")
        button_frame.columnconfigure((0, 1), weight=1)

        ttk.Button(button_frame, text="Iniciar", command=self._start).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
            pady=(0, 8),
        )
        ttk.Button(button_frame, text="Pausar", command=self._pause).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 8),
        )
        ttk.Button(button_frame, text="Reanudar", command=self._resume).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        ttk.Button(button_frame, text="Reiniciar", command=self._reset).grid(
            row=1,
            column=1,
            sticky="ew",
        )

    def _start(self) -> None:
        try:
            minutes = int(self._minutes_var.get())
            seconds = int(self._seconds_var.get())
            self._timer.set_duration(minutes, seconds)
            self._timer.start()
        except ValueError:
            self._status_var.set("Ingrese una duraci\u00f3n valida.")
            return

        self._status_var.set("Temporizador en marcha.")

    def _pause(self) -> None:
        self._timer.pause()
        self._status_var.set("Temporizador pausado.")

    def _resume(self) -> None:
        self._timer.resume()
        self._status_var.set("Temporizador en marcha.")

    def _reset(self) -> None:
        self._timer.reset()
        self._status_var.set("Temporizador reiniciado.")

    def _update_display(self) -> None:
        self._time_var.set(self._timer.formatted_time())
        self._draw_progress(self._timer.progress_fraction())

        if self._timer.consume_finished():
            self._status_var.set("Temporizador finalizado.")
            self._on_finished()

        self.after(100, self._update_display)

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
