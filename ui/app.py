from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk

from models.clock_marker import ClockMarker
from services.alarm_manager import AlarmManager
from services.clock_engine import ClockEngine
from ui.analog_clock_canvas import AnalogClockCanvas
from ui.control_panel import ControlPanel


class ClockApp(tk.Tk):
    """Main application window that coordinates services and widgets."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Reloj analogico con alarma")
        self.geometry("840x540")
        self.minsize(760, 500)
        self.configure(bg="#eef2f3")

        self._clock_engine = ClockEngine()
        self._alarm_manager = AlarmManager()
        self._selected_marker: ClockMarker = self._clock_engine.find_marker(12)
        self._alarm_notice_until = 0.0
        self._notice_showing = False

        self._configure_style()
        self._build_layout()
        self._sync_panel_state()
        self._update_clock()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#eef2f3")
        style.configure("TLabelframe", background="#eef2f3", bordercolor="#b7c4c1")
        style.configure("TLabelframe.Label", background="#eef2f3", foreground="#263238")
        style.configure("TLabel", background="#eef2f3", foreground="#263238")
        style.configure("TButton", padding=(10, 6))
        style.configure("TSpinbox", padding=4)

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=18)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)
        container.rowconfigure(0, weight=1)

        self._clock_canvas = AnalogClockCanvas(container)
        self._clock_canvas.grid(row=0, column=0, sticky="nsew")

        self._control_panel = ControlPanel(
            container,
            on_set_alarm=self._set_alarm,
            on_enable_alarm=self._enable_alarm,
            on_disable_alarm=self._disable_alarm,
            on_previous_marker=self._select_previous_marker,
            on_next_marker=self._select_next_marker,
            on_current_marker=self._select_current_marker,
            on_clear_notice=self._clear_alarm_notice,
        )
        self._control_panel.grid(row=0, column=1, sticky="ns", padx=(18, 0))

    def _update_clock(self) -> None:
        moment = self._clock_engine.get_current_time()
        angles = self._clock_engine.calculate_hand_angles(moment)

        if self._alarm_manager.check_alarm(moment):
            self._start_alarm_notice()

        alarm_visible = time.monotonic() < self._alarm_notice_until
        if self._notice_showing and not alarm_visible:
            self._control_panel.hide_alarm_notice()
            self._notice_showing = False
            self._control_panel.set_message("Listo")

        self._clock_canvas.render(
            moment=moment,
            angles=angles,
            markers=self._clock_engine.iter_markers_forward(),
            selected_marker=self._selected_marker,
            alarm_visible=alarm_visible,
        )
        self.after(200, self._update_clock)

    def _set_alarm(self, hour: int, minute: int) -> None:
        try:
            alarm = self._alarm_manager.set_alarm(hour, minute)
        except ValueError:
            self._control_panel.set_message("La alarma no es valida.")
            return

        self._control_panel.set_alarm_status(self._alarm_manager.status_text())
        self._control_panel.set_message(f"Alarma guardada para {alarm.formatted_time()}")

    def _enable_alarm(self) -> None:
        try:
            self._alarm_manager.enable_alarm()
        except ValueError:
            self._control_panel.set_message("Configure una alarma primero.")
            return

        self._sync_panel_state()
        self._control_panel.set_message("Alarma activada.")

    def _disable_alarm(self) -> None:
        try:
            self._alarm_manager.disable_alarm()
        except ValueError:
            self._control_panel.set_message("Configure una alarma primero.")
            return

        self._sync_panel_state()
        self._control_panel.set_message("Alarma desactivada.")

    def _select_previous_marker(self) -> None:
        self._selected_marker = self._clock_engine.get_previous_marker(self._selected_marker)
        self._sync_panel_state()

    def _select_next_marker(self) -> None:
        self._selected_marker = self._clock_engine.get_next_marker(self._selected_marker)
        self._sync_panel_state()

    def _select_current_marker(self) -> None:
        self._selected_marker = self._clock_engine.marker_for_datetime(
            self._clock_engine.get_current_time()
        )
        self._sync_panel_state()

    def _start_alarm_notice(self) -> None:
        alarm = self._alarm_manager.alarm
        if alarm is None:
            return

        self._alarm_notice_until = time.monotonic() + 8
        self._notice_showing = True
        self.bell()
        self._control_panel.show_alarm_notice(alarm.formatted_time())

    def _clear_alarm_notice(self) -> None:
        self._alarm_notice_until = 0.0
        self._notice_showing = False
        self._control_panel.hide_alarm_notice()
        self._control_panel.set_message("Aviso cerrado.")

    def _sync_panel_state(self) -> None:
        self._control_panel.set_alarm_status(self._alarm_manager.status_text())
        self._control_panel.set_marker_status(self._selected_marker.hour)
