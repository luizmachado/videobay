import json
import os
import tempfile
from pathlib import Path

from videobay_gui.core.videobay_user_settings import (
    VideobayUserSettings,
    parse_videobay_user_settings_document,
    serialize_videobay_user_settings,
)

CORRUPTED_SETTINGS_BACKUP_SUFFIX = ".bak"


class JsonFileVideobaySettingsStoreAdapter:
    def __init__(self, settings_file_path: Path, default_output_directory: str) -> None:
        self.settings_file_path = settings_file_path
        self.default_output_directory = default_output_directory

    def load_videobay_user_settings(self) -> VideobayUserSettings:
        try:
            settings_file_text = self.settings_file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return VideobayUserSettings(preferred_output_directory=self.default_output_directory)
        try:
            raw_settings_document = json.loads(settings_file_text)
        except json.JSONDecodeError:
            # WHY: keep the broken file for the user to inspect instead of losing it (EC-15).
            self.settings_file_path.replace(
                self.settings_file_path.with_name(
                    self.settings_file_path.name + CORRUPTED_SETTINGS_BACKUP_SUFFIX
                )
            )
            return VideobayUserSettings(preferred_output_directory=self.default_output_directory)
        return parse_videobay_user_settings_document(
            raw_settings_document, self.default_output_directory
        )

    def save_videobay_user_settings(self, videobay_user_settings: VideobayUserSettings) -> None:
        self.settings_file_path.parent.mkdir(parents=True, exist_ok=True)
        serialized_settings_text = json.dumps(
            serialize_videobay_user_settings(videobay_user_settings), ensure_ascii=False, indent=2
        )
        # WHY: write-to-temp + os.replace is atomic, so a crash mid-save never leaves a
        # truncated settings file behind (which would otherwise trigger EC-15 on next start).
        temporary_file_descriptor, temporary_settings_path = tempfile.mkstemp(
            dir=self.settings_file_path.parent, prefix=".settings-", suffix=".tmp"
        )
        with os.fdopen(temporary_file_descriptor, "w", encoding="utf-8") as temporary_settings_file:
            temporary_settings_file.write(serialized_settings_text)
        os.replace(temporary_settings_path, self.settings_file_path)
