from videobay_gui.core.video_download_job_row_view_model import VideoDownloadJobRowViewModel


class RecordingVideoDownloadQueueViewFake:
    def __init__(self) -> None:
        self.shown_output_directories: list[str] = []
        self.shown_download_notices: list[str | None] = []
        self.shown_job_rows: list[VideoDownloadJobRowViewModel] = []

    def show_output_directory(self, output_directory: str) -> None:
        self.shown_output_directories.append(output_directory)

    def show_download_notice(self, download_notice_message: str | None) -> None:
        self.shown_download_notices.append(download_notice_message)

    def show_video_download_job_row(
        self, video_download_job_row_view_model: VideoDownloadJobRowViewModel
    ) -> None:
        self.shown_job_rows.append(video_download_job_row_view_model)

    def latest_row_of_job(self, video_download_job_identifier: int) -> VideoDownloadJobRowViewModel:
        return [
            shown_job_row
            for shown_job_row in self.shown_job_rows
            if shown_job_row.video_download_job_identifier == video_download_job_identifier
        ][-1]

    def status_labels_of_job(self, video_download_job_identifier: int) -> list[str]:
        return [
            shown_job_row.job_status_label
            for shown_job_row in self.shown_job_rows
            if shown_job_row.video_download_job_identifier == video_download_job_identifier
        ]
