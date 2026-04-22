from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class NumericFieldValidator:
    """Registers Tkinter validation commands for numeric entry widgets."""

    def __init__(self, master: tk.Misc) -> None:
        self._master = master

    def create_digit_command(self, max_digits: int) -> str:
        return self._master.register(
            lambda proposed: self._is_digit_input_valid(proposed, max_digits)
        )

    def create_range_command(self, min_value: int, max_value: int, max_digits: int) -> str:
        return self._master.register(
            lambda proposed: self._is_range_input_valid(
                proposed,
                min_value,
                max_value,
                max_digits,
            )
        )

    def attach_focus_normalizer(
        self,
        widget: ttk.Spinbox,
        variable: tk.StringVar,
        min_value: int,
        max_value: int,
        on_invalid: Callable[[str], None],
        allow_empty_as_zero: bool,
    ) -> None:
        widget.bind(
            "<FocusOut>",
            lambda _event: self.normalize_value(
                variable,
                min_value,
                max_value,
                on_invalid,
                allow_empty_as_zero,
            ),
        )

    def normalize_value(
        self,
        variable: tk.StringVar,
        min_value: int,
        max_value: int,
        on_invalid: Callable[[str], None],
        allow_empty_as_zero: bool,
    ) -> bool:
        raw_value = variable.get()
        stripped_value = raw_value.strip()

        if stripped_value == "":
            if allow_empty_as_zero:
                variable.set("00")
                return True
            on_invalid("Complete los campos numericos.")
            return False

        if not stripped_value.isdigit():
            on_invalid("Solo se permiten numeros.")
            return False

        value = int(stripped_value)
        if not min_value <= value <= max_value:
            on_invalid(f"El valor debe estar entre {min_value} y {max_value}.")
            return False

        variable.set(f"{value:02d}")
        return True

    def _is_digit_input_valid(self, proposed: str, max_digits: int) -> bool:
        if proposed == "":
            return True
        return proposed.isdigit() and len(proposed) <= max_digits

    def _is_range_input_valid(
        self,
        proposed: str,
        min_value: int,
        max_value: int,
        max_digits: int,
    ) -> bool:
        if proposed == "":
            return True
        if not proposed.isdigit() or len(proposed) > max_digits:
            return False
        return min_value <= int(proposed) <= max_value
