# Analog Clock Workshop

Desktop analog clock application built entirely with Python, Tkinter, and Canvas.
It has no HTML, CSS, JavaScript, webviews, or external runtime dependencies.

## Project Structure

```text
analog_clock_workshop/
├── main.py
├── requirements.txt
├── README.md
├── data_structures/
│   ├── __init__.py
│   └── doubly_circular_linked_list.py
├── models/
│   ├── __init__.py
│   ├── alarm.py
│   └── clock_marker.py
├── services/
│   ├── __init__.py
│   ├── alarm_manager.py
│   └── clock_engine.py
└── ui/
    ├── __init__.py
    ├── analog_clock_canvas.py
    ├── app.py
    └── control_panel.py
```

## Architecture

- `data_structures` contains the custom `DoublyCircularLinkedList` and node class.
- `models` contains small domain objects: `ClockMarker` and `Alarm`.
- `services` contains application logic for time calculations and alarm validation.
- `ui` contains Tkinter widgets: the canvas clock, side control panel, and main window.
- `main.py` is the entry point.

## Object-Oriented Design

The application separates responsibilities into focused classes:

- `ClockEngine` calculates hand angles and owns the circular sequence of hour markers.
- `AlarmManager` creates, enables, disables, and checks alarms.
- `AnalogClockCanvas` draws the analog face, markers, hands, and visual alarm notice.
- `ControlPanel` handles user controls and visible status messages.
- `ClockApp` coordinates the services and UI update cycle.

This keeps drawing code, domain logic, data structure logic, and application wiring in
separate modules.

## Doubly Circular Linked List Usage

The 12 major hour positions are represented as a custom doubly circular linked list.
`ClockEngine` builds the marker ring in clock order: 12, 1, 2, ..., 11.

This structure is used in two real parts of the application:

1. The canvas draws hour labels by traversing the marker ring forward.
2. The control panel buttons move the selected marker forward and backward through
   the same circular links.

Because the clock face is circular, the data structure naturally models the domain:
after 11 comes 12 again, and before 12 comes 11.

## Alarm Feature

The user can set an alarm time, enable it, disable it, and see Spanish status
messages. When the alarm matches the local system time, the app shows a red visual
notification on the clock and uses Python-only sound options (`winsound` on Windows
or a terminal bell fallback).

## How to Run

Use Python 3 with Tkinter available:

```bash
python main.py
```

No dependency installation is needed because the project uses only the Python
standard library.
