from typing import Any

from videobay_gui.core.download_progress_snapshot import DownloadProgressViewModel


class RecordingSingleMediaDownloadViewFake:
    def __init__(self) -> None:
        self.recorded_view_calls: list[tuple[str, Any]] = []

    def show_output_directory(self, output_directory: str) -> None:
        self.recorded_view_calls.append(("show_output_directory", output_directory))

    def show_download_notice(self, download_notice_message: str | None) -> None:
        self.recorded_view_calls.append(("show_download_notice", download_notice_message))

    def show_download_in_progress(self) -> None:
        self.recorded_view_calls.append(("show_download_in_progress", None))

    def show_download_progress(
        self, download_progress_view_model: DownloadProgressViewModel
    ) -> None:
        self.recorded_view_calls.append(("show_download_progress", download_progress_view_model))

    def show_download_completed(self, download_completed_message: str) -> None:
        self.recorded_view_calls.append(("show_download_completed", download_completed_message))

    def show_download_failure(
        self, download_failure_message: str, can_retry_download: bool
    ) -> None:
        self.recorded_view_calls.append(
            ("show_download_failure", (download_failure_message, can_retry_download))
        )

    def show_download_cancelled(self) -> None:
        self.recorded_view_calls.append(("show_download_cancelled", None))

    def recorded_view_call_names(self) -> list[str]:
        return [view_call_name for view_call_name, _ in self.recorded_view_calls]

    def recorded_arguments_of(self, view_call_name: str) -> list[Any]:
        return [
            view_call_argument
            for recorded_call_name, view_call_argument in self.recorded_view_calls
            if recorded_call_name == view_call_name
        ]
