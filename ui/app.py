from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk

from models.clock_marker import ClockMarker
from models.clock_theme import ClockTheme
from services.alarm_manager import AlarmManager
from services.clock_engine import ClockEngine
from services.theme_manager import ThemeManager
from services.world_time_service import WorldTimeService
from ui.alarm_popup import AlarmPopup
from ui.analog_clock_canvas import AnalogClockCanvas
from ui.control_panel import ControlPanel


class ClockApp(tk.Tk):
    """Main application window that coordinates services and widgets."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Reloj analogico con alarma")
        self.geometry("1020x660")
        self.minsize(920, 620)

        self._clock_engine = ClockEngine()
        self._alarm_manager = AlarmManager()
        self._theme_manager = ThemeManager()
        self._world_time_service = WorldTimeService()
        self._current_theme = self._theme_manager.get_default_theme()
        self._selected_marker: ClockMarker = self._clock_engine.find_marker(12)
        self._alarm_notice_until = 0.0
        self._notice_showing = False
        self._alarm_popup: AlarmPopup | None = None

        self._configure_style()
        self._build_layout()
        self._apply_theme(self._current_theme)
        self._sync_panel_state()
        self._update_clock()

    def _configure_style(self) -> None:
        self._style = ttk.Style(self)
        self._style.theme_use("clam")
        self._style.configure("TButton", padding=(10, 6))
        self._style.configure("TSpinbox", padding=4)

    def _build_layout(self) -> None:
        self._container = ttk.Frame(self, padding=18)
        self._container.pack(fill=tk.BOTH, expand=True)
        self._container.columnconfigure(0, weight=1)
        self._container.columnconfigure(1, weight=0)
        self._container.rowconfigure(0, weight=1)

        self._clock_canvas = AnalogClockCanvas(self._container, theme=self._current_theme)
        self._clock_canvas.grid(row=0, column=0, sticky="nsew")

        self._control_panel = ControlPanel(
            self._container,
            themes=self._theme_manager.get_themes(),
            on_set_alarm=self._set_alarm,
            on_enable_alarm=self._enable_alarm,
            on_disable_alarm=self._disable_alarm,
            on_theme_change=self._change_theme,
            on_previous_marker=self._select_previous_marker,
            on_next_marker=self._select_next_marker,
            on_current_marker=self._select_current_marker,
        )
        self._control_panel.grid(row=0, column=1, sticky="ns", padx=(18, 0))

    def _update_clock(self) -> None:
        moment = self._clock_engine.get_current_time()
        angles = self._clock_engine.calculate_hand_angles(moment)
        alarm = self._alarm_manager.check_alarm(moment)

        if alarm is not None:
            self._start_alarm_notice(alarm.formatted_time())

        alarm_visible = time.monotonic() < self._alarm_notice_until
        if self._notice_showing and not alarm_visible:
            self._control_panel.hide_alarm_notice()
            self._notice_showing = False

        self._control_panel.update_world_times(
            self._world_time_service.get_snapshots(moment)
        )
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

        self._close_alarm_popup()
        self._clear_alarm_notice()
        self._sync_panel_state()
        self._control_panel.set_message("Alarma desactivada.")

    def _snooze_alarm(self, minutes: int) -> None:
        try:
            self._alarm_manager.snooze_alarm(minutes, self._clock_engine.get_current_time())
        except ValueError:
            self._control_panel.set_message("Configure una alarma primero.")
            return

        self._close_alarm_popup()
        self._clear_alarm_notice()
        self._sync_panel_state()
        self._control_panel.set_message(f"Alarma postergada {minutes} minutos.")

    def _change_theme(self, display_name: str) -> None:
        try:
            theme = self._theme_manager.find_by_display_name(display_name)
        except LookupError:
            self._control_panel.set_message("Tema no encontrado.")
            return

        self._current_theme = theme
        self._apply_theme(theme)
        self._clock_canvas.set_theme(theme)
        self._control_panel.set_message(f"Tema aplicado: {theme.display_name}")

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

    def _start_alarm_notice(self, alarm_time: str) -> None:
        self._alarm_notice_until = time.monotonic() + 20
        self._notice_showing = True
        self._alarm_manager.play_notification_sound()
        self.bell()
        self._control_panel.show_alarm_notice(alarm_time)
        self._show_alarm_popup(alarm_time)

    def _show_alarm_popup(self, alarm_time: str) -> None:
        if self._alarm_popup is not None and self._alarm_popup.winfo_exists():
            self._alarm_popup.lift()
            return

        self._alarm_popup = AlarmPopup(
            self,
            alarm_time=alarm_time,
            on_disable=self._disable_alarm,
            on_snooze_five=lambda: self._snooze_alarm(5),
            on_snooze_ten=lambda: self._snooze_alarm(10),
        )

    def _close_alarm_popup(self) -> None:
        if self._alarm_popup is not None and self._alarm_popup.winfo_exists():
            self._alarm_popup.destroy()
        self._alarm_popup = None

    def _clear_alarm_notice(self) -> None:
        self._alarm_notice_until = 0.0
        self._notice_showing = False
        self._control_panel.hide_alarm_notice()

    def _sync_panel_state(self) -> None:
        self._control_panel.set_alarm_status(self._alarm_manager.status_text())
        self._control_panel.set_marker_status(self._selected_marker.hour)

    def _apply_theme(self, theme: ClockTheme) -> None:
        self.configure(bg=theme.background_color)
        self._style.configure("TFrame", background=theme.background_color)
        self._style.configure(
            "TLabelframe",
            background=theme.background_color,
            bordercolor=theme.inner_border_color,
        )
        self._style.configure(
            "TLabelframe.Label",
            background=theme.background_color,
            foreground=theme.border_color,
        )
        self._style.configure(
            "TLabel",
            background=theme.background_color,
            foreground=theme.border_color,
        )
