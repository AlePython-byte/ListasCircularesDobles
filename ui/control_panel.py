from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Iterable, Optional, Tuple

from models.alarm import Alarm
from models.clock_theme import ClockTheme
from models.world_clock import WorldClockEntry, WorldTimeSnapshot
from ui.countdown_timer_panel import CountdownTimerPanel
from ui.numeric_validation import NumericFieldValidator
from ui.stopwatch_panel import StopwatchPanel


class ControlPanel(ttk.Frame):
    """Right-side notebook that organizes clock controls by feature."""

    PANEL_WIDTH = 370
    TAB_PADDING = (16, 16, 16, 14)
    SECTION_PADDING = 12
    SECTION_GAP = 12
    CONTENT_WRAP_LENGTH = 305
    ALARM_TABLE_HEIGHT = 6
    ALARM_LABEL_MAX_LENGTH = Alarm.MAX_LABEL_LENGTH

    def __init__(
        self,
        master: tk.Misc,
        themes: Iterable[ClockTheme],
        timezone_entries: Iterable[WorldClockEntry],
        on_add_alarm: Callable[[int, int, str], None],
        on_update_alarm: Callable[[int, int, int, str], bool],
        on_enable_alarm: Callable[[int], None],
        on_disable_alarm: Callable[[int], None],
        on_delete_alarm: Callable[[int], None],
        on_theme_change: Callable[[str], None],
        on_timezone_change: Callable[[str], None],
        on_timer_finished: Callable[[], None],
    ) -> None:
        super().__init__(master, padding=0)
        self.configure(width=self.PANEL_WIDTH)
        self.grid_propagate(False)
        self._themes = tuple(themes)
        self._timezone_entries = tuple(timezone_entries)
        self._on_add_alarm = on_add_alarm
        self._on_update_alarm = on_update_alarm
        self._on_enable_alarm = on_enable_alarm
        self._on_disable_alarm = on_disable_alarm
        self._on_delete_alarm = on_delete_alarm
        self._on_theme_change = on_theme_change
        self._on_timezone_change = on_timezone_change
        self._on_timer_finished = on_timer_finished
        self._validator = NumericFieldValidator(self)

        self._hour_var = tk.StringVar(value="07")
        self._minute_var = tk.StringVar(value="00")
        self._label_var = tk.StringVar(value="")
        self._alarm_form_help_var = tk.StringVar(
            value="Complete la hora en la zona seleccionada; la etiqueta es opcional."
        )
        self._alarm_summary_var = tk.StringVar(value="No hay alarmas programadas.")
        self._next_alarm_var = tk.StringVar(value="Proxima alarma: ninguna")
        self._selected_alarm_var = tk.StringVar(value="Seleccione una alarma para editarla.")
        self._message_var = tk.StringVar(value="Listo")
        self._theme_var = tk.StringVar(value=self._themes[0].display_name)
        self._timezone_var = tk.StringVar(value=self._timezone_entries[0].city)
        self._world_time_vars: Dict[str, tk.StringVar] = {}
        self._alarm_by_id: Dict[int, Alarm] = {}
        self._alarm_enabled_by_id: Dict[int, bool] = {}
        self._editing_alarm_id: Optional[int] = None
        self._alarm_tree: Optional[ttk.Treeview] = None
        self._alarm_form_frame: ttk.LabelFrame | None = None
        self._add_alarm_button: ttk.Button | None = None
        self._cancel_edit_button: ttk.Button | None = None
        self._enable_alarm_button: ttk.Button | None = None
        self._disable_alarm_button: ttk.Button | None = None
        self._delete_alarm_button: ttk.Button | None = None

        self._build_layout()
        self._bind_alarm_validation()
        self._set_alarm_form_mode(editing=False)
        self._update_alarm_button_states()

    def get_alarm_values(self) -> Tuple[int, int, str]:
        raw_hour = self._hour_var.get().strip()
        raw_minute = self._minute_var.get().strip()

        if raw_hour == "" or raw_minute == "":
            raise ValueError("Complete la hora y el minuto de la alarma.")
        if not raw_hour.isdigit() or not raw_minute.isdigit():
            raise ValueError("Use valores numericos para la alarma.")

        hour = int(raw_hour)
        minute = int(raw_minute)

        if not 0 <= hour <= 23:
            raise ValueError("La hora debe estar entre 0 y 23.")
        if not 0 <= minute <= 59:
            raise ValueError("El minuto debe estar entre 0 y 59.")

        try:
            label = Alarm.normalize_label(self._label_var.get())
        except ValueError:
            raise ValueError(
                f"La etiqueta debe tener maximo {self.ALARM_LABEL_MAX_LENGTH} caracteres."
            ) from None

        self._hour_var.set(f"{hour:02d}")
        self._minute_var.set(f"{minute:02d}")
        self._label_var.set(label)
        return hour, minute, label

    def set_alarm_summary(self, text: str) -> None:
        self._alarm_summary_var.set(text)

    def set_next_alarm_text(self, text: str) -> None:
        self._next_alarm_var.set(text)

    def set_theme_selection(self, display_name: str) -> None:
        self._theme_var.set(display_name)

    def set_timezone_selection(self, city: str) -> None:
        self._timezone_var.set(city)

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

        selected_id = self.get_selected_alarm_id() or self._editing_alarm_id
        alarm_items = tuple(alarms)
        self._alarm_by_id = {}
        self._alarm_enabled_by_id = {}
        for item_id in self._alarm_tree.get_children():
            self._alarm_tree.delete(item_id)

        for alarm in alarm_items:
            item_id = str(alarm.alarm_id)
            self._alarm_by_id[alarm.alarm_id] = alarm
            self._alarm_enabled_by_id[alarm.alarm_id] = alarm.enabled
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
        else:
            if self._editing_alarm_id is not None:
                self._exit_alarm_edit_mode(clear_selection=False)
            current_selection = self._alarm_tree.selection()
            if current_selection:
                self._alarm_tree.selection_remove(current_selection)

        self._update_alarm_button_states()

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
        self.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew", ipadx=2, ipady=2)

        alarms_tab = ttk.Frame(notebook, padding=self.TAB_PADDING)
        stopwatch_tab = StopwatchPanel(notebook)
        timer_tab = CountdownTimerPanel(notebook, on_finished=self._on_timer_finished)
        world_tab = ttk.Frame(notebook, padding=self.TAB_PADDING)

        notebook.add(alarms_tab, text="Alarmas")
        notebook.add(stopwatch_tab, text="Cron\u00f3metro")
        notebook.add(timer_tab, text="Temporizador")
        notebook.add(world_tab, text="Horas mundiales")
        notebook.select(alarms_tab)

        self._build_alarms_tab(alarms_tab)
        self._build_world_tab(world_tab)

    def _build_alarms_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

        self._build_timezone_frame(tab, row=0)
        self._build_alarm_form_frame(tab, row=1)
        self._build_alarm_list_frame(tab, row=2)
        self._build_status_frame(tab, row=3)

    def _build_timezone_frame(self, parent: ttk.Frame, row: int) -> None:
        timezone_frame = ttk.LabelFrame(
            parent,
            text="Zona horaria del reloj",
            padding=self.SECTION_PADDING,
        )
        timezone_frame.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, self.SECTION_GAP),
        )
        timezone_frame.columnconfigure(0, weight=1)

        timezone_combo = ttk.Combobox(
            timezone_frame,
            textvariable=self._timezone_var,
            values=tuple(entry.city for entry in self._timezone_entries),
            state="readonly",
        )
        timezone_combo.grid(row=0, column=0, sticky="ew")
        timezone_combo.bind("<<ComboboxSelected>>", self._handle_timezone_change)

    def _build_alarm_form_frame(self, parent: ttk.Frame, row: int) -> None:
        form_frame = ttk.LabelFrame(
            parent,
            text="Agregar alarma",
            padding=self.SECTION_PADDING,
        )
        self._alarm_form_frame = form_frame
        form_frame.grid(row=row, column=0, sticky="ew", pady=(0, self.SECTION_GAP))
        form_frame.columnconfigure((0, 1), weight=1)
        hour_validation = self._validator.create_range_command(0, 23, 2)
        minute_validation = self._validator.create_range_command(0, 59, 2)

        ttk.Label(
            form_frame,
            textvariable=self._alarm_form_help_var,
            wraplength=self.CONTENT_WRAP_LENGTH,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(form_frame, text="Hora").grid(row=1, column=0, sticky="w")
        ttk.Label(form_frame, text="Minuto").grid(row=1, column=1, sticky="w")

        hour_spinbox = ttk.Spinbox(
            form_frame,
            from_=0,
            to=23,
            textvariable=self._hour_var,
            width=6,
            format="%02.0f",
            validate="key",
            validatecommand=(hour_validation, "%P"),
        )
        hour_spinbox.grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(4, 10))

        minute_spinbox = ttk.Spinbox(
            form_frame,
            from_=0,
            to=59,
            textvariable=self._minute_var,
            width=6,
            format="%02.0f",
            validate="key",
            validatecommand=(minute_validation, "%P"),
        )
        minute_spinbox.grid(row=2, column=1, sticky="ew", pady=(4, 10))
        self._validator.attach_focus_normalizer(
            hour_spinbox,
            self._hour_var,
            0,
            23,
            self.set_message,
            allow_empty_as_zero=False,
        )
        self._validator.attach_focus_normalizer(
            minute_spinbox,
            self._minute_var,
            0,
            59,
            self.set_message,
            allow_empty_as_zero=False,
        )

        ttk.Label(form_frame, text="Etiqueta").grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
        )
        label_validation = self.register(self._is_label_text_allowed)
        label_invalid_command = self.register(self._show_label_validation_message)
        label_entry = ttk.Entry(
            form_frame,
            textvariable=self._label_var,
            validate="key",
            validatecommand=(label_validation, "%P"),
            invalidcommand=label_invalid_command,
        )
        label_entry.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(4, 4),
        )
        ttk.Label(
            form_frame,
            text=f"Opcional, maximo {self.ALARM_LABEL_MAX_LENGTH} caracteres.",
            font=("Segoe UI", 8),
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 10))

        form_button_frame = ttk.Frame(form_frame)
        form_button_frame.grid(row=6, column=0, columnspan=2, sticky="ew")
        form_button_frame.columnconfigure((0, 1), weight=1)

        self._add_alarm_button = ttk.Button(
            form_button_frame,
            text="Agregar alarma",
            command=self._handle_alarm_form_submit,
        )
        self._add_alarm_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._cancel_edit_button = ttk.Button(
            form_button_frame,
            text="Cancelar",
            command=self._cancel_alarm_edit,
        )
        self._cancel_edit_button.grid(row=0, column=1, sticky="ew")

    def _build_alarm_list_frame(self, parent: ttk.Frame, row: int) -> None:
        list_frame = ttk.LabelFrame(
            parent,
            text="Alarmas programadas",
            padding=self.SECTION_PADDING,
        )
        list_frame.grid(row=row, column=0, sticky="nsew", pady=(0, self.SECTION_GAP))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(3, weight=1)

        ttk.Label(list_frame, textvariable=self._alarm_summary_var).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 7),
        )
        ttk.Label(
            list_frame,
            textvariable=self._next_alarm_var,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(
            list_frame,
            textvariable=self._selected_alarm_var,
            wraplength=self.CONTENT_WRAP_LENGTH,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 8))

        columns = ("time", "label", "status")
        self._alarm_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=self.ALARM_TABLE_HEIGHT,
            selectmode="browse",
        )
        self._alarm_tree.heading("time", text="Hora")
        self._alarm_tree.heading("label", text="Etiqueta")
        self._alarm_tree.heading("status", text="Estado")
        self._alarm_tree.column("time", width=62, anchor=tk.CENTER, stretch=False)
        self._alarm_tree.column("label", width=142, anchor=tk.W)
        self._alarm_tree.column("status", width=96, anchor=tk.W, stretch=False)
        self._alarm_tree.grid(row=3, column=0, sticky="nsew")
        self._alarm_tree.bind(
            "<<TreeviewSelect>>",
            self._handle_alarm_selection,
        )
        tree_scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self._alarm_tree.yview,
        )
        tree_scrollbar.grid(row=3, column=1, sticky="ns")
        self._alarm_tree.configure(yscrollcommand=tree_scrollbar.set)

        action_frame = ttk.Frame(list_frame)
        action_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        action_frame.columnconfigure((0, 1, 2), weight=1)

        self._enable_alarm_button = ttk.Button(
            action_frame,
            text="Activar",
            command=self._handle_enable_alarm,
        )
        self._enable_alarm_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )
        self._disable_alarm_button = ttk.Button(
            action_frame,
            text="Desactivar",
            command=self._handle_disable_alarm,
        )
        self._disable_alarm_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(0, 8),
        )
        self._delete_alarm_button = ttk.Button(
            action_frame,
            text="Eliminar",
            command=self._handle_delete_alarm,
        )
        self._delete_alarm_button.grid(
            row=0,
            column=2,
            sticky="ew",
        )

    def _build_world_tab(self, tab: ttk.Frame) -> None:
        tab.columnconfigure(0, weight=1)

        world_frame = ttk.LabelFrame(
            tab,
            text="Horas mundiales",
            padding=self.SECTION_PADDING,
        )
        world_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.SECTION_GAP))
        world_frame.columnconfigure(0, weight=1)

        for index, entry in enumerate(self._timezone_entries):
            value = tk.StringVar(value=f"{entry.city}: --:--:--")
            self._world_time_vars[entry.city] = value
            ttk.Label(
                world_frame,
                textvariable=value,
                font=("Segoe UI", 10),
                wraplength=self.CONTENT_WRAP_LENGTH,
            ).grid(row=index, column=0, sticky="w", pady=(0, 9))

        theme_frame = ttk.LabelFrame(
            tab,
            text="Apariencia del reloj",
            padding=self.SECTION_PADDING,
        )
        theme_frame.grid(row=1, column=0, sticky="ew")
        theme_frame.columnconfigure(0, weight=1)

        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self._theme_var,
            values=tuple(theme.display_name for theme in self._themes),
            state="readonly",
        )
        theme_combo.grid(row=0, column=0, sticky="ew")
        theme_combo.bind("<<ComboboxSelected>>", self._handle_theme_change)

    def _build_status_frame(self, parent: ttk.Frame, row: int) -> None:
        status_frame = ttk.LabelFrame(parent, text="Estado", padding=self.SECTION_PADDING)
        status_frame.grid(row=row, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        ttk.Label(
            status_frame,
            textvariable=self._message_var,
            wraplength=self.CONTENT_WRAP_LENGTH,
        ).grid(row=0, column=0, sticky="w")

    def _handle_alarm_form_submit(self) -> None:
        try:
            hour, minute, label = self.get_alarm_values()
        except ValueError as error:
            self.set_message(str(error))
            return

        if self._editing_alarm_id is None:
            self._on_add_alarm(hour, minute, label)
            return

        updated = self._on_update_alarm(self._editing_alarm_id, hour, minute, label)
        if updated:
            self._exit_alarm_edit_mode(clear_selection=True)

    def _handle_enable_alarm(self) -> None:
        alarm_id = self.get_selected_alarm_id()
        if alarm_id is None:
            self.set_message("Seleccione una alarma de la lista.")
            return
        self._on_enable_alarm(alarm_id)

    def _handle_disable_alarm(self) -> None:
        alarm_id = self.get_selected_alarm_id()
        if alarm_id is None:
            self.set_message("Seleccione una alarma de la lista.")
            return
        self._on_disable_alarm(alarm_id)

    def _handle_delete_alarm(self) -> None:
        alarm_id = self.get_selected_alarm_id()
        if alarm_id is None:
            self.set_message("Seleccione una alarma de la lista.")
            return
        self._on_delete_alarm(alarm_id)

    def _handle_alarm_selection(self, _event: tk.Event) -> None:
        alarm_id = self.get_selected_alarm_id()
        if alarm_id is None:
            self._selected_alarm_var.set("Seleccione una alarma para editarla.")
            self._update_alarm_button_states()
            return

        alarm = self._alarm_by_id.get(alarm_id)
        if alarm is not None:
            self._enter_alarm_edit_mode(alarm)

        self._update_alarm_button_states()

    def _enter_alarm_edit_mode(self, alarm: Alarm) -> None:
        self._editing_alarm_id = alarm.alarm_id
        self._hour_var.set(f"{alarm.hour:02d}")
        self._minute_var.set(f"{alarm.minute:02d}")
        self._label_var.set(alarm.label)
        self._set_alarm_form_mode(editing=True)
        self._selected_alarm_var.set(
            f"Seleccionada: {alarm.formatted_time()} - {alarm.display_label()}"
        )
        self.set_message(f"Editando alarma: {alarm.formatted_time()} - {alarm.display_label()}")

    def _exit_alarm_edit_mode(self, clear_selection: bool) -> None:
        self._editing_alarm_id = None
        self._hour_var.set("07")
        self._minute_var.set("00")
        self._label_var.set("")
        self._set_alarm_form_mode(editing=False)
        self._selected_alarm_var.set("Seleccione una alarma para editarla.")

        if clear_selection and self._alarm_tree is not None:
            selection = self._alarm_tree.selection()
            if selection:
                self._alarm_tree.selection_remove(selection)

        self._update_alarm_button_states()

    def _cancel_alarm_edit(self) -> None:
        if self._editing_alarm_id is None:
            return
        self._exit_alarm_edit_mode(clear_selection=True)
        self.set_message("Edicion cancelada.")

    def _set_alarm_form_mode(self, editing: bool) -> None:
        if self._alarm_form_frame is not None:
            self._alarm_form_frame.configure(
                text="Editar alarma" if editing else "Agregar alarma"
            )
        self._alarm_form_help_var.set(
            "Modo edicion: ajuste la hora en la zona seleccionada."
            if editing
            else "Complete la hora en la zona seleccionada; la etiqueta es opcional."
        )
        if self._add_alarm_button is not None:
            self._add_alarm_button.configure(
                text="Guardar cambios" if editing else "Agregar alarma"
            )
            self._add_alarm_button.grid_configure(
                column=0,
                columnspan=1 if editing else 2,
                padx=(0, 8) if editing else (0, 0),
            )
        if self._cancel_edit_button is not None:
            if editing:
                self._cancel_edit_button.grid(row=0, column=1, sticky="ew")
            else:
                self._cancel_edit_button.grid_remove()
        self._set_button_state(self._cancel_edit_button, editing)

    def _handle_theme_change(self, _event: tk.Event) -> None:
        self._on_theme_change(self._theme_var.get())

    def _handle_timezone_change(self, _event: tk.Event) -> None:
        self._on_timezone_change(self._timezone_var.get())

    def _bind_alarm_validation(self) -> None:
        for variable in (self._hour_var, self._minute_var, self._label_var):
            variable.trace_add("write", lambda *_args: self._update_alarm_button_states())

    def _update_alarm_button_states(self) -> None:
        self._set_button_state(self._add_alarm_button, self._is_alarm_input_valid())
        self._set_button_state(self._cancel_edit_button, self._editing_alarm_id is not None)
        selected_id = self.get_selected_alarm_id()
        has_selection = selected_id is not None
        selected_enabled = self._alarm_enabled_by_id.get(selected_id, False)
        self._set_button_state(self._enable_alarm_button, has_selection and not selected_enabled)
        self._set_button_state(self._disable_alarm_button, has_selection and selected_enabled)
        self._set_button_state(self._delete_alarm_button, has_selection)

    def _is_alarm_input_valid(self) -> bool:
        hour = self._hour_var.get().strip()
        minute = self._minute_var.get().strip()
        if hour == "" or minute == "":
            return False
        if not hour.isdigit() or not minute.isdigit():
            return False
        return (
            0 <= int(hour) <= 23
            and 0 <= int(minute) <= 59
            and self._is_label_value_valid()
        )

    def _is_label_text_allowed(self, proposed_value: str) -> bool:
        if len(proposed_value) > self.ALARM_LABEL_MAX_LENGTH:
            return False
        return all(character.isprintable() for character in proposed_value)

    def _show_label_validation_message(self) -> None:
        self.set_message(
            f"La etiqueta debe tener maximo {self.ALARM_LABEL_MAX_LENGTH} caracteres."
        )

    def _is_label_value_valid(self) -> bool:
        try:
            Alarm.normalize_label(self._label_var.get())
        except ValueError:
            return False
        return True

    def _set_button_state(self, button: ttk.Button | None, enabled: bool) -> None:
        if button is not None:
            button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def _format_alarm_status(self, alarm: Alarm) -> str:
        if not alarm.enabled:
            return "Inactiva"
        if alarm.snooze_until is not None:
            return f"Postergada {alarm.snooze_until.strftime('%H:%M')}"
        return "Activa"
