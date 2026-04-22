# Analog Clock Workshop

Desktop analog clock application built entirely with Python, Tkinter, and Canvas.
It has no HTML, CSS, JavaScript, webviews, or external runtime dependencies.

## Project Structure

```text
analog_clock_workshop/
|-- main.py
|-- requirements.txt
|-- README.md
|-- data_structures/
|   |-- __init__.py
|   `-- doubly_circular_linked_list.py
|-- models/
|   |-- __init__.py
|   |-- alarm.py
|   |-- clock_marker.py
|   |-- clock_theme.py
|   `-- world_clock.py
|-- services/
|   |-- __init__.py
|   |-- alarm_manager.py
|   |-- clock_engine.py
|   |-- theme_manager.py
|   `-- world_time_service.py
`-- ui/
    |-- __init__.py
    |-- alarm_popup.py
    |-- analog_clock_canvas.py
    |-- app.py
    `-- control_panel.py
```

## Architecture

- `data_structures` contains the custom `DoublyCircularLinkedList` and node class.
- `models` contains domain objects for alarms, markers, themes, and world clocks.
- `services` contains application logic for time, alarm storage, themes, and time zones.
- `ui` contains Tkinter widgets for the canvas, control panel, popup, and main window.
- `main.py` is the entry point.

## Object-Oriented Design

The application separates responsibilities into focused classes:

- `ClockEngine` calculates analog hand angles and owns the circular hour marker ring.
- `AlarmManager` stores multiple alarms and handles enable, disable, delete, snooze,
  and trigger checks.
- `WorldTimeService` uses `zoneinfo` to resolve supported time zones.
- `ThemeManager` exposes predefined visual themes.
- `AnalogClockCanvas` draws the analog clock using the selected theme.
- `ControlPanel` displays the right-side selector, alarm form, alarm list, actions,
  world times, theme selector, and status messages.
- `AlarmPopup` provides alarm actions when an alarm triggers.
- `ClockApp` coordinates services and widgets through Tkinter's update loop.

## User Interface

The layout has two main panels:

- Left panel: large analog clock, selected time zone label, and a small reference time.
- Right panel: time zone selector, alarm creation form, scheduled alarms table,
  alarm action buttons, world times, theme selector, and status area.

The old marker panel was removed from the GUI to keep the interface focused on
practical controls.

## Doubly Circular Linked List Usage

The 12 major hour positions are still represented as a custom doubly circular
linked list. `ClockEngine` builds the marker ring in clock order: 12, 1, 2, ...,
11.

This structure remains meaningful internally:

1. The canvas draws hour labels by traversing the marker ring forward.
2. The app highlights the current hour marker for the selected time zone by
   resolving that hour through the same circular marker structure.

The data structure is not exposed as a separate user control anymore, but it still
models the circular nature of the analog clock face.

## Time Zones

The selected time zone controls the analog clock itself. The app supports:

- Bogota (`America/Bogota`)
- New York (`America/New_York`)
- London (`Europe/London`)
- Tokyo (`Asia/Tokyo`)

The implementation uses Python's standard `zoneinfo` module with safe fixed-offset
fallbacks if IANA timezone data is unavailable.

## Multiple Alarms

Users can create multiple alarms. Each alarm stores an id, hour, minute, optional
label, enabled state, last-triggered minute, and snooze target. The scheduled alarms
panel uses a Tkinter `Treeview` so each saved alarm can be selected, activated,
deactivated, or deleted independently.

When an enabled alarm reaches its configured time in the currently selected time
zone, the app plays a Python-only notification sound, shows a visual alert on the
clock, and opens a popup with actions to disable the alarm or snooze it for 5 or
10 minutes. Trigger keys prevent repeated broken triggers during the same minute.

## Themes

The analog clock supports predefined themes: classic, dark, blue, and green. Themes
control the clock face, border, hands, marker colors, selected hour marker, and
alarm highlight color.

## How to Run

Use Python 3 with Tkinter available:

```bash
python main.py
```

No dependency installation is needed because the project uses only the Python
standard library.
