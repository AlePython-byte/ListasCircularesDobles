from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class TimerPopup(tk.Toplevel):
    """Popup shown when the countdown timer reaches zero."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.title("Temporizador")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._build_layout()
        self._center_on_master(master)
        self.lift()
        self.focus_force()

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=20)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)

        ttk.Label(
            container,
            text="Temporizador finalizado",
            font=("Segoe UI", 16, "bold"),
            foreground="#c62828",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        ttk.Label(
            container,
            text="El tiempo programado ha terminado.",
            font=("Segoe UI", 11),
        ).grid(row=1, column=0, sticky="w", pady=(0, 16))

        ttk.Button(container, text="Aceptar", command=self.destroy).grid(
            row=2,
            column=0,
            sticky="ew",
        )

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
