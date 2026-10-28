from collections.abc import Callable
from typing import Any, Protocol

from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome


class MediaDownloadExecutorPort(Protocol):
    def execute_media_download(
        self,
        media_url: str,
        yt_dlp_download_options: dict[str, Any],
        on_download_progress: Callable[[DownloadProgressSnapshot], None],
        is_download_cancellation_requested: Callable[[], bool],
    ) -> MediaDownloadOutcome:
        """Blocking call on a worker thread.

        Raises MediaDownloadCancelledError when cancellation was requested (EC-09) and
        MediaDownloadFailedError for every other failure. on_download_progress runs on the
        worker thread; callers must hop to the UI thread themselves (ADR-0004).
        """
        ...
