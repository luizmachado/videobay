from typing import Protocol

from videobay_gui.core.videobay_user_settings import VideobayUserSettings


class VideobaySettingsStorePort(Protocol):
    def load_videobay_user_settings(self) -> VideobayUserSettings:
        """Never raises: unreadable or invalid storage yields defaults (EC-15)."""
        ...

    def save_videobay_user_settings(self, videobay_user_settings: VideobayUserSettings) -> None: ...
