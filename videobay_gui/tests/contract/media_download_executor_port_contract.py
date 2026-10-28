import pytest

from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_download_failure import MediaDownloadCancelledError
from videobay_gui.ports.media_download_executor_port import MediaDownloadExecutorPort


class MediaDownloadExecutorPortContract:
    """Shared by the scripted fake and (under -m integration) the real yt-dlp executor.

    Subclasses provide an executor plus a URL and options that download a small real file.
    """

    def build_executor_under_contract(self) -> MediaDownloadExecutorPort:
        raise NotImplementedError

    def downloadable_media_url(self) -> str:
        raise NotImplementedError

    def download_options_for_contract(self) -> dict[str, object]:
        raise NotImplementedError

    def test_reports_progress_and_returns_downloaded_files(self):
        received_progress_snapshots: list[DownloadProgressSnapshot] = []

        media_download_outcome = self.build_executor_under_contract().execute_media_download(
            self.downloadable_media_url(),
            dict(self.download_options_for_contract()),
            received_progress_snapshots.append,
            lambda: False,
        )

        assert received_progress_snapshots
        assert media_download_outcome.downloaded_file_paths
        assert media_download_outcome.was_already_downloaded is False

    def test_ec09_requested_cancellation_raises_cancelled_error(self):
        with pytest.raises(MediaDownloadCancelledError):
            self.build_executor_under_contract().execute_media_download(
                self.downloadable_media_url(),
                dict(self.download_options_for_contract()),
                lambda _progress_snapshot: None,
                lambda: True,
            )
