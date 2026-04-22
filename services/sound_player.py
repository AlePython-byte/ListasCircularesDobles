from __future__ import annotations

from pathlib import Path


class AlarmSoundPlayer:
    """Plays and stops alarm sounds on Windows using winsound."""

    def __init__(self) -> None:
        self._is_playing = False
        self._sound_path = Path(__file__).resolve().parent.parent / "assets" / "sonido_Guitarra.wav"

    def start_loop(self) -> None:
        if self._is_playing:
            return

        try:
            import winsound

            if self._sound_path.exists():
                winsound.PlaySound(
                    str(self._sound_path),
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP,
                )
            else:
                winsound.PlaySound(
                    "SystemExclamation",
                    winsound.SND_ALIAS | winsound.SND_ASYNC | winsound.SND_LOOP,
                )

            self._is_playing = True
        except Exception:
            self._is_playing = False

    def stop(self) -> None:
        try:
            import winsound

            winsound.PlaySound(None, 0)
        except Exception:
            pass

        self._is_playing = False

    @property
    def is_playing(self) -> bool:
        return self._is_playing