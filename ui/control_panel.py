from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Iterable, Optional, Tuple

from models.alarm import Alarm
from models.clock_theme import ClockTheme
from models.world_clock import WorldClockEntry, WorldTimeSnapshot


class ControlPanel(ttk.Frame):
    """Right panel for time zones, alarm management, themes, and status."""

    def __init__(
        self,
        master: tk.Misc,
        themes: Iterable[ClockTheme],
        timezone_entries: Iterable[WorldClockEntry],
        on_add_alarm: Callable[[int, int, str], None],
        on_enable_alarm: Callable[[int], None],
        on_disable_alarm: Callable[[int], None],
        on_delete_alarm: Callable[[int], None],
        on_theme_change: Callable[[str], None],
        on_timezone_change: Callable[[str], None],
    ) -> None:
        super().__init__(master, padding=16)
        self._themes = tuple(themes)
        self._timezone_entries = tuple(timezone_entries)
        self._on_add_alarm = on_add_alarm
        self._on_enable_alarm = on_enable_alarm
        self._on_disable_alarm = on_disable_alarm
        self._on_delete_alarm = on_delete_alarm
        self._on_theme_change = on_theme_change
        self._on_timezone_change = on_timezone_change

        self._hour_var = tk.StringVar(value="07")
        self._minute_var = tk.StringVar(value="00")
        self._label_var = tk.StringVar(value="")
        self._alarm_summary_var = tk.StringVar(value="No hay alarmas programadas.")
        self._message_var = tk.StringVar(value="Listo")
        self._theme_var = tk.StringVar(value=self._themes[0].display_name)
        self._timezone_var = tk.StringVar(value=self._timezone_entries[0].city)
        self._world_time_vars: Dict[str, tk.StringVar] = {}
        self._alarm_tree: Optional[ttk.Treeview] = None

        self._build_layout()

    def get_alarm_values(self) -> Tuple[int, int, str]:
        try:
            hour = int(self._hour_var.get())
            minute = int(self._minute_var.get())
        except ValueError as exc:
            raise ValueError("Use valores numericos para la alarma.") from exc

        if not 0 <= hour <= 23:
            raise ValueError("La hora debe estar entre 0 y 23.")
        if not 0 <= minute <= 59:
            raise ValueError("El minuto debe estar entre 0 y 59.")

        return hour, minute, self._label_var.get().strip()

    def set_alarm_summary(self, text: str) -> None:
        self._alarm_summary_var.set(text)

    def set_message(self, text: str) -> None:
        self._message_var.set(text)

    def show_alarm_notice(self, alarm: Alarm) -> None:
        self._message_var.set(
            f"Alarma sonando: {alarm.formatted_time()} - {alarm.display_label()}"
        )

    def hide_alarm_notice(self) -> None:
        self._message_var.set("Listo")

    def update_alarms(self, alarms: Iterable[Alarm]) -> None:
        if self._alarm_tree is None:
            return

        selected_id = self.get_selected_alarm_id()
        for item_id in self._alarm_tree.get_children():
            self._alarm_tree.delete(item_id)

        for alarm in alarms:
            item_id = str(alarm.alarm_id)
            self._alarm_tree.insert(
                "",
                tk.END,
                iid=item_id,
                values=(
                    alarm.formatted_time(),
                    alarm.display_label(),
                    self._format_alarm_status(alarm),
                ),
            )

        if selected_id is not None and self._alarm_tree.exists(str(selected_id)):
            self._alarm_tree.selection_set(str(selected_id))

    def update_world_times(self, snapshots: Iterable[WorldTimeSnapshot]) -> None:
        for snapshot in snapshots:
            text = (
                f"{snapshot.city}: {snapshot.time_text}\n"
                f"{snapshot.country} | {snapshot.date_text} | {snapshot.zone_text}"
            )
            if snapshot.city in self._world_time_vars:
                self._world_time_vars[snapshot.city].set(text)

    def get_selected_alarm_id(self) -> Optional[int]:
        if self._alarm_tree is None:
            return None

        selection = self._alarm_tree.selection()
        if not selection:
            return None

        return int(selection[0])

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)

        title = ttk.Label(
            self,
            text="Panel de control",
            font=("Segoe UI", 18, "bold"),
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self._build_timezone_frame(row=1)
        self._build_alarm_form_frame(row=2)
        self._build_alarm_list_frame(row=3)
        self._build_world_time_frame(row=4)
        self._build_theme_frame(row=5)
        self._build_status_frame(row=6)

    def _build_timezone_frame(self, row: int) -> None:
        timezone_frame = ttk.LabelFrame(self, text="Zona horaria del reloj", padding=10)
        timezone_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        timezone_frame.columnconfigure(0, weight=1)

        timezone_combo = ttk.Combobox(
            timezone_frame,
            textvariable=self._timezone_var,
            values=tuple(entry.city for entry in self._timezone_entries),
            state="readonly",
        )
        timezone_combo.grid(row=0, column=0, sticky="ew")
        timezone_combo.bind("<<ComboboxSelected>>", self._handle_timezone_change)

    def _build_alarm_form_frame(self, row: int) -> None:
        form_frame = ttk.LabelFrame(self, text="Agregar alarma", padding=10)
        form_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        form_frame.columnconfigure((0, 1), weight=1)

        ttk.Label(form_frame, text="Hora").grid(row=0, column=0, sticky="w")
        ttk.Label(form_frame, text="Minuto").grid(row=0, column=1, sticky="w")

        hour_spinbox = ttk.Spinbox(
            form_frame,
            from_=0,
            to=23,
            textvariable=self._hour_var,
            width=6,
            format="%02.0f",
        )
        hour_spinbox.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(3, 8))

        minute_spinbox = ttk.Spinbox(
            form_frame,
            from_=0,
            to=59,
            textvariable=self._minute_var,
            width=6,
            format="%02.0f",
        )
        minute_spinbox.grid(row=1, column=1, sticky="ew", pady=(3, 8))

        ttk.Label(form_frame, text="Etiqueta").grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
        )
        label_entry = ttk.Entry(form_frame, textvariable=self._label_var)
        label_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(3, 8))

        add_button = ttk.Button(
            form_frame,
            text="Agregar alarma",
            command=self._handle_add_alarm,
        )
        add_button.grid(row=4, column=0, columnspan=2, sticky="ew")

    def _build_alarm_list_frame(self, row: int) -> None:
        list_frame = ttk.LabelFrame(self, text="Alarmas programadas", padding=10)
        list_frame.grid(row=row, column=0, sticky="nsew", pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)

        summary_label = ttk.Label(list_frame, textvariable=self._alarm_summary_var)
        summary_label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        columns = ("time", "label", "status")
        self._alarm_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=6,
            selectmode="browse",
        )
        self._alarm_tree.heading("time", text="Hora")
        self._alarm_tree.heading("label", text="Etiqueta")
        self._alarm_tree.heading("status", text="Estado")
        self._alarm_tree.column("time", width=58, anchor=tk.CENTER, stretch=False)
        self._alarm_tree.column("label", width=112, anchor=tk.W)
        self._alarm_tree.column("status", width=88, anchor=tk.W)
        self._alarm_tree.grid(row=1, column=0, sticky="ew")

        action_frame = ttk.Frame(list_frame)
        action_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        action_frame.columnconfigure((0, 1, 2), weight=1)

        enable_button = ttk.Button(
            action_frame,
            text="Activar",
            command=self._handle_enable_alarm,
        )
        enable_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        disable_button = ttk.Button(
            action_frame,
            text="Desactivar",
            command=self._handle_disable_alarm,
        )
        disable_button.grid(row=0, column=1, sticky="ew", padx=(0, 6))

        delete_button = ttk.Button(
            action_frame,
            text="Eliminar",
            command=self._handle_delete_alarm,
        )
        delete_button.grid(row=0, column=2, sticky="ew")

    def _build_world_time_frame(self, row: int) -> None:
        world_frame = ttk.LabelFrame(self, text="Horas mundiales", padding=10)
        world_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        world_frame.columnconfigure(0, weight=1)

        for index, entry in enumerate(self._timezone_entries):
            value = tk.StringVar(value=f"{entry.city}: --:--:--")
            self._world_time_vars[entry.city] = value
            label = ttk.Label(
                world_frame,
                textvariable=value,
                font=("Segoe UI", 9),
                wraplength=275,
            )
            label.grid(row=index, column=0, sticky="w", pady=(0, 5))

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

    def _build_status_frame(self, row: int) -> None:
        status_frame = ttk.LabelFrame(self, text="Estado", padding=10)
        status_frame.grid(row=row, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        message_label = ttk.Label(
            status_frame,
            textvariable=self._message_var,
            wraplength=275,
        )
        message_label.grid(row=0, column=0, sticky="w")

    def _handle_add_alarm(self) -> None:
        try:
            hour, minute, label = self.get_alarm_values()
        except ValueError as error:
            self.set_message(str(error))
            return

        self._on_add_alarm(hour, minute, label)

    def _handle_enable_alarm(self) -> None:
        alarm_id = self.get_selected_alarm_id()
        if alarm_id is None:
            self.set_message("Seleccione una alarma.")
            return
        self._on_enable_alarm(alarm_id)

    def _handle_disable_alarm(self) -> None:
        alarm_id = self.get_selected_alarm_id()
        if alarm_id is None:
            self.set_message("Seleccione una alarma.")
            return
        self._on_disable_alarm(alarm_id)

    def _handle_delete_alarm(self) -> None:
        alarm_id = self.get_selected_alarm_id()
        if alarm_id is None:
            self.set_message("Seleccione una alarma.")
            return
        self._on_delete_alarm(alarm_id)

    def _handle_theme_change(self, _event: tk.Event) -> None:
        self._on_theme_change(self._theme_var.get())

    def _handle_timezone_change(self, _event: tk.Event) -> None:
        self._on_timezone_change(self._timezone_var.get())

    def _format_alarm_status(self, alarm: Alarm) -> str:
        if not alarm.enabled:
            return "Inactiva"
        if alarm.snooze_until is not None:
            return f"Postergada {alarm.snooze_until.strftime('%H:%M')}"
        return "Activa"
