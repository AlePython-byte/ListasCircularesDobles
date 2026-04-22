class SoundService:
    """Plays notification sounds with standard-library fallbacks."""

    def play_notification_sound(self) -> None:
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            print("\a", end="")
