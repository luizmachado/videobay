from dataclasses import replace

from videobay_gui.core.videobay_user_settings import describe_output_directory_problem_for_user
from videobay_gui.ports.output_directory_access_probe_port import OutputDirectoryAccessProbePort
from videobay_gui.ports.videobay_settings_store_port import VideobaySettingsStorePort


class VideobayOutputDirectoryPreference:
    """Where downloads go: the saved folder plus the EC-06 checks before using or saving it."""

    def __init__(
        self,
        videobay_settings_store: VideobaySettingsStorePort,
        output_directory_access_probe: OutputDirectoryAccessProbePort,
    ) -> None:
        self.videobay_settings_store = videobay_settings_store
        self.output_directory_access_probe = output_directory_access_probe

    def load_preferred_output_directory(self) -> str:
        return self.videobay_settings_store.load_videobay_user_settings().preferred_output_directory

    def find_output_directory_problem_message(self, output_directory: str) -> str | None:
        output_directory_problem = self.output_directory_access_probe.find_output_directory_problem(
            output_directory
        )
        if output_directory_problem is None:
            return None
        return describe_output_directory_problem_for_user(
            output_directory_problem, output_directory
        )

    def save_preferred_output_directory(self, output_directory: str) -> None:
        self.videobay_settings_store.save_videobay_user_settings(
            replace(
                self.videobay_settings_store.load_videobay_user_settings(),
                preferred_output_directory=output_directory,
            )
        )
