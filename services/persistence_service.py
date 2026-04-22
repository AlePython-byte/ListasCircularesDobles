from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class PersistenceService:
    """Loads and saves application state as JSON."""

    def __init__(self, file_path: Path | None = None) -> None:
        self._file_path = file_path or Path("data") / "app_state.json"

    def load_state(self) -> Dict[str, Any]:
        if not self._file_path.exists():
            return {}

        try:
            with self._file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(data, dict):
            return {}
        return data

    def save_state(self, state: Dict[str, Any]) -> None:
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            with self._file_path.open("w", encoding="utf-8") as file:
                json.dump(state, file, indent=2, ensure_ascii=False)
        except OSError:
            return
