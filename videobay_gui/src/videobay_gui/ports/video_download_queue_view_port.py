from typing import Protocol

from videobay_gui.core.video_download_job_row_view_model import VideoDownloadJobRowViewModel


class VideoDownloadQueueViewPort(Protocol):
    def show_output_directory(self, output_directory: str) -> None: ...

    def show_download_notice(self, download_notice_message: str | None) -> None: ...

    def show_video_download_job_row(
        self, video_download_job_row_view_model: VideoDownloadJobRowViewModel
    ) -> None:
        """Adds the row the first time an identifier is seen and updates it afterwards."""
        ...
