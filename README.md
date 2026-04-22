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
- `models` contains domain objects for markers, alarms, themes, and world clocks.
- `services` contains application logic for time, alarm, theme, and world time behavior.
- `ui` contains Tkinter widgets for the canvas, control panel, popup, and main window.
- `main.py` is the entry point.

## Object-Oriented Design

The application separates responsibilities into focused classes:

- `ClockEngine` calculates analog hand angles and owns the circular hour marker ring.
- `AlarmManager` creates, enables, disables, checks, and snoozes alarms.
- `WorldTimeService` uses `zoneinfo` to produce live times for major world cities.
- `ThemeManager` exposes predefined visual themes.
- `AnalogClockCanvas` draws the analog clock using the selected theme.
- `ControlPanel` displays alarm controls, world times, themes, marker traversal, and status.
- `AlarmPopup` provides alarm actions when the alarm triggers.
- `ClockApp` coordinates services and widgets through Tkinter's update loop.

## Doubly Circular Linked List Usage

The 12 major hour positions are represented as a custom doubly circular linked list.
`ClockEngine` builds the marker ring in clock order: 12, 1, 2, ..., 11.

This structure is used in two real parts of the application:

1. The canvas draws hour labels by traversing the marker ring forward.
2. The "Recorrido circular" panel moves the selected marker forward and backward
   through the same circular links.

Because the clock face is circular, the data structure naturally models the domain:
after 11 comes 12 again, and before 12 comes 11.

## World Time

The interface shows live times for New York, London, and Tokyo. The implementation
uses Python's standard `zoneinfo` module with safe fixed-offset fallbacks if the
local environment does not provide IANA timezone data.

## Themes

The analog clock supports predefined themes: classic, dark, blue, and green. Themes
control the clock face, border, hands, marker colors, selected marker, and alarm
highlight color.

## Alarm Feature

The user can set an alarm, enable it, disable it, and receive Spanish status
messages. When the alarm triggers, the app plays a Python-only notification sound,
shows a visual alert on the clock, and opens a popup with actions to disable the
alarm or snooze it for 5 or 10 minutes. The alarm tracks the last triggered minute
to avoid repeated broken triggers.

## How to Run

Use Python 3 with Tkinter available:

```bash
python main.py
```

No dependency installation is needed because the project uses only the Python
standard library.
