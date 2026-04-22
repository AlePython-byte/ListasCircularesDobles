from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from models.stopwatch import Stopwatch


class StopwatchPanel(ttk.Frame):
    """Notebook tab that displays and controls a visual stopwatch."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=16)
        self._stopwatch = Stopwatch()
        self._time_var = tk.StringVar(value="00:00:00.0")
        self._status_var = tk.StringVar(value="Listo")
        self._start_button: ttk.Button | None = None
        self._pause_button: ttk.Button | None = None
        self._resume_button: ttk.Button | None = None
        self._reset_button: ttk.Button | None = None
        self._build_layout()
        self._update_button_states()
        self._update_display()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)

        title = ttk.Label(
            self,
            text="Cron\u00f3metro",
            font=("Segoe UI", 15, "bold"),
            anchor=tk.CENTER,
        )
        title.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self._progress_canvas = tk.Canvas(
            self,
            width=190,
            height=190,
            bg="#eef2f3",
            highlightthickness=0,
        )
        self._progress_canvas.grid(row=1, column=0, pady=(0, 10))

        time_label = ttk.Label(
            self,
            textvariable=self._time_var,
            font=("Segoe UI", 28, "bold"),
            anchor=tk.CENTER,
        )
        time_label.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        status_label = ttk.Label(
            self,
            textvariable=self._status_var,
            anchor=tk.CENTER,
        )
        status_label.grid(row=3, column=0, sticky="ew", pady=(0, 14))

        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, sticky="ew")
        button_frame.columnconfigure((0, 1), weight=1)

        self._start_button = ttk.Button(button_frame, text="Iniciar", command=self._start)
        self._start_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
            pady=(0, 8),
        )
        self._pause_button = ttk.Button(button_frame, text="Pausar", command=self._pause)
        self._pause_button.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(0, 8),
        )
        self._resume_button = ttk.Button(button_frame, text="Reanudar", command=self._resume)
        self._resume_button.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        self._reset_button = ttk.Button(button_frame, text="Reiniciar", command=self._reset)
        self._reset_button.grid(
            row=1,
            column=1,
            sticky="ew",
        )

    def _start(self) -> None:
        self._stopwatch.start()
        self._status_var.set("Cron\u00f3metro en marcha.")
        self._update_button_states()

    def _pause(self) -> None:
        self._stopwatch.pause()
        self._status_var.set("Cron\u00f3metro pausado.")
        self._update_button_states()

    def _resume(self) -> None:
        self._stopwatch.resume()
        self._status_var.set("Cron\u00f3metro en marcha.")
        self._update_button_states()

    def _reset(self) -> None:
        self._stopwatch.reset()
        self._status_var.set("Listo")
        self._update_button_states()

    def _update_display(self) -> None:
        self._time_var.set(self._stopwatch.formatted_time())
        self._draw_progress(self._stopwatch.progress_fraction())
        self.after(100, self._update_display)

    def _update_button_states(self) -> None:
        state = self._stopwatch.state
        self._set_button_state(self._start_button, state == "idle")
        self._set_button_state(self._pause_button, state == "running")
        self._set_button_state(self._resume_button, state == "paused")
        self._set_button_state(self._reset_button, state in ("running", "paused"))

    def _set_button_state(self, button: ttk.Button | None, enabled: bool) -> None:
        if button is not None:
            button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def _draw_progress(self, fraction: float) -> None:
        self._progress_canvas.delete("all")
        pad = 15
        size = 190
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
            extent=-fraction * 360,
            style=tk.ARC,
            outline="#2f80ed",
            width=12,
        )
        self._progress_canvas.create_text(
            size / 2,
            size / 2,
            text="60 s",
            fill="#263238",
            font=("Segoe UI", 11, "bold"),
        )
