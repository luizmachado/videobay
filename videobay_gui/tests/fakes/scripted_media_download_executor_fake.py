from collections.abc import Callable
from typing import Any

from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_download_failure import MediaDownloadCancelledError
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome


class ScriptedMediaDownloadExecutorFake:
    """Emits scripted progress snapshots, honouring cancellation between them like yt-dlp hooks."""

    def __init__(self) -> None:
        self.scripted_progress_snapshots: list[DownloadProgressSnapshot] = []
        self.scripted_outcome = MediaDownloadOutcome(("/tmp/video.mp4",), False)
        self.scripted_download_error: Exception | None = None
        self.executed_downloads: list[tuple[str, dict[str, Any]]] = []

    def execute_media_download(
        self,
        media_url: str,
        yt_dlp_download_options: dict[str, Any],
        on_download_progress: Callable[[DownloadProgressSnapshot], None],
        is_download_cancellation_requested: Callable[[], bool],
    ) -> MediaDownloadOutcome:
        self.executed_downloads.append((media_url, yt_dlp_download_options))
        for scripted_progress_snapshot in self.scripted_progress_snapshots:
            if is_download_cancellation_requested():
                raise MediaDownloadCancelledError(media_url)
            on_download_progress(scripted_progress_snapshot)
        # PROVENANCE: yt-dlp always fires a final "finished" hook, where the real adapter checks
        # cancellation too, so a cancel request is honoured even without progress events.
        if is_download_cancellation_requested():
            raise MediaDownloadCancelledError(media_url)
        if self.scripted_download_error is not None:
            raise self.scripted_download_error
        return self.scripted_outcome
