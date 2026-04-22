from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class AlarmPopup(tk.Toplevel):
    """Popup shown when the alarm is triggered."""

    def __init__(
        self,
        master: tk.Misc,
        alarm_time: str,
        on_disable: Callable[[], None],
        on_snooze_five: Callable[[], None],
        on_snooze_ten: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.title("Alarma")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", on_snooze_five)

        self._on_disable = on_disable
        self._on_snooze_five = on_snooze_five
        self._on_snooze_ten = on_snooze_ten

        self._build_layout(alarm_time)
        self._center_on_master(master)
        self.lift()
        self.focus_force()

    def _build_layout(self, alarm_time: str) -> None:
        container = ttk.Frame(self, padding=20)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)

        title = ttk.Label(
            container,
            text="Alarma activada",
            font=("Segoe UI", 16, "bold"),
            foreground="#c62828",
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 8))

        message = ttk.Label(
            container,
            text=f"Es la hora programada: {alarm_time}",
            font=("Segoe UI", 11),
        )
        message.grid(row=1, column=0, sticky="w", pady=(0, 16))

        disable_button = ttk.Button(
            container,
            text="Desactivar alarma",
            command=self._on_disable,
        )
        disable_button.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        snooze_five_button = ttk.Button(
            container,
            text="Postergar 5 minutos",
            command=self._on_snooze_five,
        )
        snooze_five_button.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        snooze_ten_button = ttk.Button(
            container,
            text="Postergar 10 minutos",
            command=self._on_snooze_ten,
        )
        snooze_ten_button.grid(row=4, column=0, sticky="ew")

    def _center_on_master(self, master: tk.Misc) -> None:
        self.update_idletasks()
        master.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()
        master_x = master.winfo_rootx()
        master_y = master.winfo_rooty()
        master_width = master.winfo_width()
        master_height = master.winfo_height()

        x = master_x + (master_width - width) // 2
        y = master_y + (master_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
