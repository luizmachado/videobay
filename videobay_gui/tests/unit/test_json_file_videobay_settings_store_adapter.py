import json
from pathlib import Path

from videobay_gui.adapters.json_file_videobay_settings_store_adapter import (
    JsonFileVideobaySettingsStoreAdapter,
)
from videobay_gui.core.videobay_user_settings import VideobayUserSettings

DEFAULT_TEST_OUTPUT_DIRECTORY = "/home/user/Downloads"


def test_ec15_corrupted_file_is_backed_up_and_defaults_are_used(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{ this is not json", encoding="utf-8")
    settings_store = JsonFileVideobaySettingsStoreAdapter(
        settings_file, DEFAULT_TEST_OUTPUT_DIRECTORY
    )

    loaded_settings = settings_store.load_videobay_user_settings()

    assert loaded_settings.preferred_output_directory == DEFAULT_TEST_OUTPUT_DIRECTORY
    assert (tmp_path / "settings.json.bak").read_text(encoding="utf-8") == "{ this is not json"
    assert not settings_file.exists()


def test_save_writes_readable_utf8_json_without_leftover_temp_files(tmp_path: Path):
    settings_file = tmp_path / "settings.json"
    settings_store = JsonFileVideobaySettingsStoreAdapter(
        settings_file, DEFAULT_TEST_OUTPUT_DIRECTORY
    )

    settings_store.save_videobay_user_settings(
        VideobayUserSettings(preferred_output_directory="/home/user/Vídeos")
    )

    assert json.loads(settings_file.read_text(encoding="utf-8"))["preferred_output_directory"] == (
        "/home/user/Vídeos"
    )
    assert "Vídeos" in settings_file.read_text(encoding="utf-8")
    assert sorted(path.name for path in tmp_path.iterdir()) == ["settings.json"]
