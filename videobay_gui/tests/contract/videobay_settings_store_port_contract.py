from videobay_gui.core.videobay_user_settings import VideobayUserSettings
from videobay_gui.ports.videobay_settings_store_port import VideobaySettingsStorePort

CONTRACT_DEFAULT_OUTPUT_DIRECTORY = "/contract/default/Downloads"
CONTRACT_CONCURRENT_DOWNLOADS = 4


class VideobaySettingsStorePortContract:
    """Subclasses build a store whose default directory is CONTRACT_DEFAULT_OUTPUT_DIRECTORY."""

    def build_settings_store_under_contract(self) -> VideobaySettingsStorePort:
        raise NotImplementedError

    def test_fresh_store_loads_defaults(self):
        loaded_settings = self.build_settings_store_under_contract().load_videobay_user_settings()

        assert loaded_settings == VideobayUserSettings(
            preferred_output_directory=CONTRACT_DEFAULT_OUTPUT_DIRECTORY
        )

    def test_saved_settings_are_loaded_back(self):
        settings_store = self.build_settings_store_under_contract()
        changed_settings = VideobayUserSettings(
            preferred_output_directory="/srv/vídeos com espaço",
            maximum_concurrent_downloads=CONTRACT_CONCURRENT_DOWNLOADS,
        )

        settings_store.save_videobay_user_settings(changed_settings)

        assert settings_store.load_videobay_user_settings() == changed_settings
