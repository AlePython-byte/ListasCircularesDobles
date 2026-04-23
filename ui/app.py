from __future__ import annotations

import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from models.alarm import Alarm
from models.clock_theme import ClockTheme
from services.alarm_manager import AlarmManager
from services.clock_engine import ClockEngine
from services.persistence_service import PersistenceService
from services.sound_player import AlarmSoundPlayer
from services.sound_service import SoundService
from services.theme_manager import ThemeManager
from services.world_time_service import WorldTimeService
from ui.alarm_popup import AlarmPopup
from ui.analog_clock_canvas import AnalogClockCanvas
from ui.control_panel import ControlPanel
from ui.timer_popup import TimerPopup


class ClockApp(tk.Tk):
    """Main application window that coordinates services and widgets."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Reloj analogico con alarmas")
        self.geometry("1180x740")
        self.minsize(1040, 680)

        self._clock_engine = ClockEngine()
        self._alarm_manager = AlarmManager()
        self._theme_manager = ThemeManager()
        self._world_time_service = WorldTimeService()
        self._sound_service = SoundService()
        self._alarm_sound_player = AlarmSoundPlayer()
        self._persistence_service = PersistenceService()
        self._current_theme = self._theme_manager.get_default_theme()
        self._selected_timezone_entry = self._world_time_service.find_entry("Bogotá")
        self._alarm_notice_until = 0.0
        self._notice_showing = False
        self._alarm_popup: AlarmPopup | None = None
        self._timer_popup: TimerPopup | None = None
        self._active_alarm_id: int | None = None
        self._pending_alarm_ids: list[int] = []

        self._selected_zone_var = tk.StringVar()
        self._selected_time_var = tk.StringVar()

        self._load_persisted_state()
        self._configure_style()
        self._build_layout()
        self._sync_saved_preferences_to_panel()
        self._apply_theme(self._current_theme)
        self._refresh_alarm_panel()
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)
        self._update_clock()

    def _configure_style(self) -> None:
        self._style = ttk.Style(self)
        self._style.theme_use("clam")
        self._style.configure("TButton", padding=(10, 6))
        self._style.configure("TSpinbox", padding=4)
        self._style.configure("TNotebook", padding=0)
        self._style.configure("TNotebook.Tab", padding=(8, 7))

    def _load_persisted_state(self) -> None:
        state = self._persistence_service.load_state()

        self._load_persisted_theme(state.get("selected_theme_key"))
        self._load_persisted_timezone(state.get("selected_timezone_city"))
        self._load_persisted_alarms(state.get("alarms", []))

    def _load_persisted_theme(self, theme_key: object) -> None:
        if not isinstance(theme_key, str):
            return

        try:
            self._current_theme = self._theme_manager.find_by_key(theme_key)
        except LookupError:
            return

    def _load_persisted_timezone(self, city: object) -> None:
        if not isinstance(city, str):
            return

        try:
            self._selected_timezone_entry = self._world_time_service.find_entry(city)
        except LookupError:
            return

    def _load_persisted_alarms(self, alarm_data: object) -> None:
        if not isinstance(alarm_data, list):
            return

        alarms = []
        for item in alarm_data:
            if not isinstance(item, dict):
                continue
            try:
                alarms.append(Alarm.from_dict(item))
            except (KeyError, TypeError, ValueError):
                continue

        self._alarm_manager.load_alarms(alarms)

    def _sync_saved_preferences_to_panel(self) -> None:
        self._control_panel.set_theme_selection(self._current_theme.display_name)
        self._control_panel.set_timezone_selection(self._selected_timezone_entry.city)

    def _save_persisted_state(self) -> None:
        self._persistence_service.save_state(
            {
                "selected_theme_key": self._current_theme.key,
                "selected_timezone_city": self._selected_timezone_entry.city,
                "alarms": [
                    alarm.to_dict()
                    for alarm in self._alarm_manager.get_alarms()
                ],
            }
        )

    def _build_layout(self) -> None:
        self._container = ttk.Frame(self, padding=(22, 20))
        self._container.pack(fill=tk.BOTH, expand=True)
        self._container.columnconfigure(0, weight=1, minsize=600)
        self._container.columnconfigure(1, weight=0, minsize=370)
        self._container.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(self._container, padding=(4, 2, 0, 2))
        left_panel.grid(row=0, column=0, sticky="nsew")
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(2, weight=1)

        selected_zone_label = ttk.Label(
            left_panel,
            textvariable=self._selected_zone_var,
            font=("Segoe UI", 16, "bold"),
            anchor=tk.CENTER,
        )
        selected_zone_label.grid(row=0, column=0, sticky="ew", pady=(2, 6))

        selected_time_label = ttk.Label(
            left_panel,
            textvariable=self._selected_time_var,
            font=("Segoe UI", 11),
            anchor=tk.CENTER,
        )
        selected_time_label.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        self._clock_canvas = AnalogClockCanvas(left_panel, theme=self._current_theme)
        self._clock_canvas.grid(row=2, column=0, sticky="nsew")

        self._control_panel = ControlPanel(
            self._container,
            themes=self._theme_manager.get_themes(),
            timezone_entries=self._world_time_service.get_entries(),
            on_add_alarm=self._add_alarm,
            on_update_alarm=self._update_alarm,
            on_enable_alarm=self._enable_alarm,
            on_disable_alarm=self._disable_alarm,
            on_delete_alarm=self._delete_alarm,
            on_theme_change=self._change_theme,
            on_timezone_change=self._change_timezone,
            on_timer_finished=self._handle_timer_finished,
        )
        self._control_panel.grid(row=0, column=1, sticky="nsew", padx=(24, 0))

    def _update_clock(self) -> None:
        selected_moment = self._get_selected_moment()
        angles = self._clock_engine.calculate_hand_angles(selected_moment)
        triggered_alarms = self._alarm_manager.check_alarms(selected_moment)

        if triggered_alarms:
            self._queue_triggered_alarms(triggered_alarms)
            self._save_persisted_state()

        alarm_visible = time.monotonic() < self._alarm_notice_until
        if self._notice_showing and not alarm_visible and self._alarm_popup is None:
            self._control_panel.hide_alarm_notice()
            self._notice_showing = False

        self._update_selected_time_labels(selected_moment)
        self._control_panel.set_next_alarm_text(self._next_alarm_text())
        self._control_panel.update_world_times(
            self._world_time_service.get_snapshots(datetime.now().astimezone())
        )
        self._clock_canvas.render(
            moment=selected_moment,
            angles=angles,
            markers=self._clock_engine.iter_markers_forward(),
            alarm_visible=alarm_visible,
        )
        self.after(200, self._update_clock)

    def _add_alarm(self, hour: int, minute: int, label: str) -> None:
        try:
            alarm = self._alarm_manager.create_alarm(hour, minute, label)
        except ValueError:
            self._control_panel.set_message("La alarma no es valida.")
            return

        self._refresh_alarm_panel()
        self._control_panel.set_message(
            f"Alarma agregada: {alarm.formatted_time()} - {alarm.display_label()}"
        )
        self._save_persisted_state()

    def _update_alarm(self, alarm_id: int, hour: int, minute: int, label: str) -> bool:
        try:
            alarm = self._alarm_manager.update_alarm(alarm_id, hour, minute, label)
        except ValueError:
            self._control_panel.set_message("La alarma no es valida.")
            return False

        self._refresh_alarm_panel()
        self._control_panel.set_message(
            f"Alarma actualizada: {alarm.formatted_time()} - {alarm.display_label()}"
        )
        self._save_persisted_state()
        return True

    def _enable_alarm(self, alarm_id: int) -> None:
        try:
            self._alarm_manager.enable_alarm(alarm_id)
        except ValueError:
            self._control_panel.set_message("Seleccione una alarma valida.")
            return

        self._refresh_alarm_panel()
        self._control_panel.set_message("Alarma activada.")
        self._save_persisted_state()

    def _disable_alarm(self, alarm_id: int) -> None:
        try:
            self._alarm_manager.disable_alarm(alarm_id)
        except ValueError:
            self._control_panel.set_message("Seleccione una alarma valida.")
            return

        if self._active_alarm_id == alarm_id:
            self._close_alarm_popup()
            self._clear_alarm_notice()

        self._refresh_alarm_panel()
        self._control_panel.set_message("Alarma desactivada.")
        self._save_persisted_state()

    def _delete_alarm(self, alarm_id: int) -> None:
        try:
            self._alarm_manager.delete_alarm(alarm_id)
        except ValueError:
            self._control_panel.set_message("Seleccione una alarma valida.")
            return

        self._pending_alarm_ids = [
            pending_alarm_id
            for pending_alarm_id in self._pending_alarm_ids
            if pending_alarm_id != alarm_id
        ]

        if self._active_alarm_id == alarm_id:
            self._close_alarm_popup()
            self._clear_alarm_notice()

        self._refresh_alarm_panel()
        self._control_panel.set_message("Alarma eliminada.")
        self._save_persisted_state()

    def _disable_active_alarm(self) -> None:
        if self._active_alarm_id is None:
            return

        self._disable_alarm(self._active_alarm_id)
        self._show_next_pending_alarm()

    def _snooze_active_alarm(self, minutes: int) -> None:
        if self._active_alarm_id is None:
            return

        try:
            self._alarm_manager.snooze_alarm(
                self._active_alarm_id,
                minutes,
                self._get_selected_moment(),
            )
        except ValueError:
            self._control_panel.set_message("Seleccione una alarma valida.")
            return

        self._close_alarm_popup()
        self._clear_alarm_notice()
        self._refresh_alarm_panel()
        self._control_panel.set_message(f"Alarma postergada {minutes} minutos.")
        self._save_persisted_state()
        self._show_next_pending_alarm()

    def _change_timezone(self, city: str) -> None:
        try:
            self._selected_timezone_entry = self._world_time_service.find_entry(city)
        except LookupError:
            self._control_panel.set_message("Zona horaria no encontrada.")
            return

        self._update_selected_time_labels(self._get_selected_moment())
        self._control_panel.set_message(f"Zona seleccionada: {city}")
        self._save_persisted_state()

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
        self._save_persisted_state()

    def _handle_timer_finished(self) -> None:
        self._sound_service.play_notification_sound()
        self.bell()
        self._show_timer_popup()

    def _queue_triggered_alarms(self, alarms: tuple[Alarm, ...]) -> None:
        for alarm in alarms:
            if (
                alarm.alarm_id != self._active_alarm_id
                and alarm.alarm_id not in self._pending_alarm_ids
            ):
                self._pending_alarm_ids.append(alarm.alarm_id)

        self._show_next_pending_alarm()

    def _show_next_pending_alarm(self) -> None:
        if self._alarm_popup is not None and self._alarm_popup.winfo_exists():
            return
        if not self._pending_alarm_ids:
            return

        alarm_id = self._pending_alarm_ids.pop(0)
        alarm = self._alarm_manager.get_alarm(alarm_id)
        if alarm is None:
            self._show_next_pending_alarm()
            return

        self._active_alarm_id = alarm.alarm_id
        self._start_alarm_notice(alarm)

    def _start_alarm_notice(self, alarm: Alarm) -> None:
        self._alarm_notice_until = time.monotonic() + 20
        self._notice_showing = True
        self._alarm_sound_player.start_loop()
        self.bell()
        self._control_panel.show_alarm_notice(alarm)
        self._show_alarm_popup(alarm)

    def _show_alarm_popup(self, alarm: Alarm) -> None:
        if self._alarm_popup is not None and self._alarm_popup.winfo_exists():
            self._alarm_popup.lift()
            return

        self._alarm_popup = AlarmPopup(
            self,
            alarm_time=alarm.formatted_time(),
            alarm_label=alarm.display_label(),
            on_disable=self._disable_active_alarm,
            on_snooze_five=lambda: self._snooze_active_alarm(5),
            on_snooze_ten=lambda: self._snooze_active_alarm(10),
        )

    def _show_timer_popup(self) -> None:
        if self._timer_popup is not None and self._timer_popup.winfo_exists():
            self._timer_popup.lift()
            return

        self._timer_popup = TimerPopup(self)
        self._timer_popup.protocol("WM_DELETE_WINDOW", self._close_timer_popup)

    def _close_timer_popup(self) -> None:
        if self._timer_popup is not None and self._timer_popup.winfo_exists():
            self._timer_popup.destroy()
        self._timer_popup = None

    def _close_alarm_popup(self) -> None:
        self._alarm_sound_player.stop()

        if self._alarm_popup is not None and self._alarm_popup.winfo_exists():
            self._alarm_popup.destroy()

        self._alarm_popup = None
        self._active_alarm_id = None

    def _clear_alarm_notice(self) -> None:
        self._alarm_notice_until = 0.0
        self._notice_showing = False
        self._control_panel.hide_alarm_notice()

    def _refresh_alarm_panel(self) -> None:
        self._control_panel.update_alarms(self._alarm_manager.get_alarms())
        self._control_panel.set_alarm_summary(self._alarm_manager.summary_text())
        self._control_panel.set_next_alarm_text(self._next_alarm_text())

    def _next_alarm_text(self) -> str:
        next_alarm = self._alarm_manager.next_active_alarm(self._get_selected_moment())
        if next_alarm is None:
            return "Proxima alarma: ninguna"
        return (
            f"Proxima alarma: {next_alarm.formatted_time()} - "
            f"{next_alarm.display_label()}"
        )

    def _get_selected_moment(self) -> datetime:
        timezone_info = self._world_time_service.get_timezone(self._selected_timezone_entry)
        return self._clock_engine.get_current_time(timezone_info)

    def _update_selected_time_labels(self, moment: datetime) -> None:
        entry = self._selected_timezone_entry
        zone_text = moment.tzname() or entry.zone_name
        self._selected_zone_var.set(
            f"Zona seleccionada: {entry.city} ({entry.zone_name})"
        )
        self._selected_time_var.set(
            f"Hora de referencia: {moment.strftime('%H:%M:%S')} | {zone_text}"
        )

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

    def _on_app_close(self) -> None:
        self._alarm_sound_player.stop()
        self.destroy()
