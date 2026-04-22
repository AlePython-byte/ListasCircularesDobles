# Analog Clock Workshop

Desktop analog clock application built entirely with Python, Tkinter, and Canvas.
It has no HTML, CSS, JavaScript, webviews, or external runtime dependencies.

## Project Structure

```text
analog_clock_workshop/
|-- main.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- data_structures/
|   |-- __init__.py
|   `-- doubly_circular_linked_list.py
|-- models/
|   |-- __init__.py
|   |-- alarm.py
|   |-- clock_marker.py
|   |-- clock_theme.py
|   |-- countdown_timer.py
|   |-- stopwatch.py
|   `-- world_clock.py
|-- services/
|   |-- __init__.py
|   |-- alarm_manager.py
|   |-- clock_engine.py
|   |-- persistence_service.py
|   |-- sound_service.py
|   |-- theme_manager.py
|   `-- world_time_service.py
`-- ui/
    |-- __init__.py
    |-- alarm_popup.py
    |-- analog_clock_canvas.py
    |-- app.py
    |-- control_panel.py
    |-- countdown_timer_panel.py
    |-- numeric_validation.py
    |-- stopwatch_panel.py
    `-- timer_popup.py
```

## Architecture

- `data_structures` contains the custom `DoublyCircularLinkedList` and node class.
- `models` contains domain objects for alarms, markers, themes, stopwatch,
  countdown timer, and world clocks.
- `services` contains application logic for alarm storage, clock calculations,
  JSON persistence, sound, themes, and time zones.
- `ui` contains Tkinter widgets for the analog clock, notebook control area,
  stopwatch, countdown timer, and popups.
- `main.py` is the entry point.

## User Interface

The window uses a two-panel layout:

- Left panel: large analog clock, selected time zone label, and small reference time.
- Right panel: a `ttk.Notebook` with four tabs:
  - `Alarmas`: time zone selector, alarm form, next-alarm indicator,
    scheduled alarms table, and actions.
  - `Cronometro`: large stopwatch display, circular progress ring, and controls.
  - `Temporizador`: duration inputs, large countdown display, progress ring, and controls.
  - `Horas mundiales`: live world times and the theme selector.

The notebook keeps the interface focused and avoids one long overloaded control
column. The default selected tab is `Alarmas`.

## Blue Marker Removal

The old visible selected-marker dot was removed from the analog clock. The clock
face now shows only the clean circular face, hour labels, tick marks, hands, center
cap, and alarm alert ring when needed.

## Doubly Circular Linked List Usage

The 12 major hour positions are still represented as a custom doubly circular
linked list. `ClockEngine` builds the marker ring in clock order: 12, 1, 2, ...,
11. The canvas traverses that structure to draw the hour labels, so the data
structure remains meaningful internally without exposing decorative marker controls.

## Multiple Alarms

Users can create multiple alarms. Each alarm stores an id, hour, minute, optional
label, enabled state, last-triggered minute, and optional snooze target. The
scheduled alarms panel uses a Tkinter `Treeview` so each saved alarm can be
selected, activated, deactivated, or deleted independently.

When an enabled alarm reaches its configured time in the selected time zone, the
app plays a standard-library notification sound, shows a visual alert on the clock,
and opens a popup with actions to disable the alarm or snooze it for 5 or 10
minutes.

## Numeric Validation

Editable numeric fields use Tkinter validation commands from
`NumericFieldValidator`. Alarm hours accept only values from 0 to 23, and alarm
minutes accept only values from 0 to 59. Timer minutes and seconds accept only
values from 0 to 59, while timer hours accept non-negative values up to 999.

The app validates during typing where possible and validates again before actions
such as adding an alarm or starting the timer. Values are normalized to two digits
when appropriate.

## Persistence

`PersistenceService` saves user data to `data/app_state.json` using JSON. The app
loads saved alarms, enabled states, labels, selected time zone, and selected theme
on startup. Missing or corrupted JSON is handled gracefully by starting with
defaults instead of crashing.

The generated state file is ignored by Git because it is user data.

## Stopwatch

`Stopwatch` uses `time.monotonic()` to support start, pause, resume, and reset.
`StopwatchPanel` displays the elapsed time prominently and draws a circular
progress ring for the current minute.

## Countdown Timer

`CountdownTimer` stores the configured duration, remaining time, paused state, and
finish detection. `CountdownTimerPanel` lets the user set hours, minutes, and
seconds, then start, pause, resume, or reset the countdown. When it reaches zero,
the app plays a sound and shows a Spanish popup.

## Time Zones

The selected time zone controls the analog clock itself. The app supports Bogota,
New York, London, and Tokyo through Python's standard `zoneinfo` module with safe
fixed-offset fallbacks.

## Themes

The analog clock supports predefined themes: classic, dark, blue, and green. Themes
control the clock face, border, hands, marker colors, center cap, and alarm
highlight color.

## How to Run

Use Python 3 with Tkinter available:

```bash
python main.py
```

No dependency installation is needed because the project uses only the Python
standard library.
