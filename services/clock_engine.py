from __future__ import annotations

from datetime import datetime
from typing import Dict, Generator, Optional

from data_structures.doubly_circular_linked_list import (
    DoublyCircularLinkedList,
    DoublyCircularNode,
)
from models.clock_marker import ClockMarker


class ClockEngine:
    """Time and marker calculations for the analog clock."""

    def __init__(self) -> None:
        self._markers: DoublyCircularLinkedList[ClockMarker] = DoublyCircularLinkedList()
        self._build_hour_markers()

    def get_current_time(self) -> datetime:
        return datetime.now()

    def calculate_hand_angles(self, moment: datetime) -> Dict[str, float]:
        second_value = moment.second + moment.microsecond / 1_000_000
        minute_value = moment.minute + second_value / 60
        hour_value = (moment.hour % 12) + minute_value / 60

        return {
            "hour": hour_value * 30,
            "minute": minute_value * 6,
            "second": second_value * 6,
        }

    def iter_markers_forward(self) -> Generator[ClockMarker, None, None]:
        yield from self._markers.iter_forward()

    def iter_markers_backward(self) -> Generator[ClockMarker, None, None]:
        yield from self._markers.iter_backward()

    def find_marker(self, hour: int) -> ClockMarker:
        node = self._find_marker_node(hour)
        return node.value

    def get_next_marker(self, marker: ClockMarker) -> ClockMarker:
        node = self._find_marker_node(marker.hour)
        return self._markers.next_value(node)

    def get_previous_marker(self, marker: ClockMarker) -> ClockMarker:
        node = self._find_marker_node(marker.hour)
        return self._markers.previous_value(node)

    def marker_for_datetime(self, moment: datetime) -> ClockMarker:
        hour = moment.hour % 12
        return self.find_marker(12 if hour == 0 else hour)

    def _build_hour_markers(self) -> None:
        # The analog face is circular, so its major markers are modeled as a
        # circular structure. Navigation controls reuse the same links that
        # define the drawing order instead of calculating artificial indexes.
        for position in range(12):
            hour = 12 if position == 0 else position
            marker = ClockMarker(
                hour=hour,
                label=str(hour),
                angle_degrees=position * 30.0,
            )
            self._markers.append(marker)

    def _find_marker_node(self, hour: int) -> DoublyCircularNode[ClockMarker]:
        if not 1 <= hour <= 12:
            raise ValueError("Hour marker must be between 1 and 12.")

        node: Optional[DoublyCircularNode[ClockMarker]] = self._markers.find_node(
            lambda marker: marker.hour == hour
        )
        if node is None:
            raise LookupError("Hour marker was not found.")
        return node
