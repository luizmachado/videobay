from videobay_gui.core.videobay_user_settings import VideobayUserSettings


class InMemoryVideobaySettingsStoreFake:
    def __init__(self, default_output_directory: str) -> None:
        self.stored_videobay_user_settings = VideobayUserSettings(
            preferred_output_directory=default_output_directory
        )
        self.save_call_count = 0

    def load_videobay_user_settings(self) -> VideobayUserSettings:
        return self.stored_videobay_user_settings

    def save_videobay_user_settings(self, videobay_user_settings: VideobayUserSettings) -> None:
        self.stored_videobay_user_settings = videobay_user_settings
        self.save_call_count += 1
