import errno
import glob
import os
from collections.abc import Callable, Iterator
from typing import Any

from yt_dlp.networking.exceptions import HTTPError, TransportError
from yt_dlp.utils import DownloadCancelled, PostProcessingError, YoutubeDLError

from videobay_gui.adapters.yt_dlp_shared_client_configuration import (
    TRANSIENT_HTTP_STATUS_CODES,
    SilencedYtDlpLoggerForGui,
    YtDlpInfoExtractingClientFactory,
    build_real_yt_dlp_info_extracting_client,
    build_yt_dlp_javascript_runtime_params,
    unwrap_original_yt_dlp_error_cause,
)
from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_download_failure import (
    MediaDownloadCancelledError,
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome

YT_DLP_DOWNLOAD_SOCKET_TIMEOUT_SECONDS = 30
DOWNLOAD_FAILURE_KINDS_BY_OS_ERRNO = {
    errno.ENOSPC: MediaDownloadFailureKind.OUTPUT_DISK_FULL,
    errno.EDQUOT: MediaDownloadFailureKind.OUTPUT_DISK_FULL,
    errno.EACCES: MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE,
    errno.EPERM: MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE,
    errno.EROFS: MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE,
}


def build_download_progress_snapshot_from_yt_dlp_hook(
    yt_dlp_progress_hook_payload: dict[str, Any],
) -> DownloadProgressSnapshot:
    exact_total_bytes = yt_dlp_progress_hook_payload.get("total_bytes")
    estimated_total_bytes = yt_dlp_progress_hook_payload.get("total_bytes_estimate")
    # PROVENANCE: yt-dlp only fills total_bytes when the server sends Content-Length; HLS/DASH
    # fragments give total_bytes_estimate instead (EC-08).
    total_byte_count = exact_total_bytes if exact_total_bytes else estimated_total_bytes
    yt_dlp_eta_seconds = yt_dlp_progress_hook_payload.get("eta")
    return DownloadProgressSnapshot(
        downloaded_byte_count=int(yt_dlp_progress_hook_payload.get("downloaded_bytes") or 0),
        total_byte_count=int(total_byte_count) if total_byte_count else None,
        is_total_byte_count_estimated=not exact_total_bytes and bool(estimated_total_bytes),
        download_speed_bytes_per_second=yt_dlp_progress_hook_payload.get("speed"),
        estimated_seconds_remaining=int(yt_dlp_eta_seconds)
        if yt_dlp_eta_seconds is not None
        else None,
    )


class YtDlpDownloadProgressTracker:
    """yt-dlp progress hook: forwards snapshots, remembers .part files, checks cancellation."""

    def __init__(
        self,
        on_download_progress: Callable[[DownloadProgressSnapshot], None],
        is_download_cancellation_requested: Callable[[], bool],
    ) -> None:
        self.on_download_progress = on_download_progress
        self.is_download_cancellation_requested = is_download_cancellation_requested
        self.observed_downloading_event_count = 0
        self.partial_download_file_paths: set[str] = set()

    def handle_yt_dlp_progress_hook(self, yt_dlp_progress_hook_payload: dict[str, Any]) -> None:
        partial_download_file_path = yt_dlp_progress_hook_payload.get("tmpfilename")
        if partial_download_file_path:
            self.partial_download_file_paths.add(partial_download_file_path)
        # PROVENANCE: yt-dlp documents raising DownloadCancelled from a progress hook as the way to
        # abort a download (YoutubeDL.py, progress_hooks docstring).
        if self.is_download_cancellation_requested():
            raise DownloadCancelled()
        if yt_dlp_progress_hook_payload.get("status") != "downloading":
            return
        self.observed_downloading_event_count += 1
        self.on_download_progress(
            build_download_progress_snapshot_from_yt_dlp_hook(yt_dlp_progress_hook_payload)
        )

    def remove_partial_download_files_after_cancellation(self) -> None:
        for partial_download_file_path in self.partial_download_file_paths:
            # WHY: the glob catches yt-dlp's siblings of the .part file (".part-Frag3", ".ytdl")
            # while glob.escape keeps titles with [brackets] from matching other files (EC-09).
            for leftover_file_path in glob.glob(glob.escape(partial_download_file_path) + "*"):
                os.remove(leftover_file_path)


class YtDlpDownloadExecutorAdapter:
    def __init__(
        self,
        yt_dlp_client_factory: YtDlpInfoExtractingClientFactory = (
            build_real_yt_dlp_info_extracting_client
        ),
        deno_executable_path: str | None = None,
    ) -> None:
        self.yt_dlp_client_factory = yt_dlp_client_factory
        self.deno_executable_path = deno_executable_path

    def execute_media_download(
        self,
        media_url: str,
        yt_dlp_download_options: dict[str, Any],
        on_download_progress: Callable[[DownloadProgressSnapshot], None],
        is_download_cancellation_requested: Callable[[], bool],
    ) -> MediaDownloadOutcome:
        download_progress_tracker = YtDlpDownloadProgressTracker(
            on_download_progress, is_download_cancellation_requested
        )
        yt_dlp_download_params = {
            **yt_dlp_download_options,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "socket_timeout": YT_DLP_DOWNLOAD_SOCKET_TIMEOUT_SECONDS,
            "logger": SilencedYtDlpLoggerForGui(),
            "progress_hooks": [download_progress_tracker.handle_yt_dlp_progress_hook],
            **build_yt_dlp_javascript_runtime_params(self.deno_executable_path),
        }
        try:
            with self.yt_dlp_client_factory(yt_dlp_download_params) as yt_dlp_client:
                yt_dlp_final_info_dict = yt_dlp_client.extract_info(media_url, download=True)
        except DownloadCancelled as yt_dlp_cancellation:
            download_progress_tracker.remove_partial_download_files_after_cancellation()
            raise MediaDownloadCancelledError(media_url) from yt_dlp_cancellation
        except YoutubeDLError as yt_dlp_error:
            raise MediaDownloadFailedError(
                classify_yt_dlp_download_error(yt_dlp_error), str(yt_dlp_error)
            ) from yt_dlp_error
        return MediaDownloadOutcome(
            downloaded_file_paths=tuple(
                collect_final_file_paths_from_yt_dlp_info(yt_dlp_final_info_dict or {})
            ),
            # WHY: yt-dlp emits no "downloading" event when the target already exists (EC-07).
            was_already_downloaded=download_progress_tracker.observed_downloading_event_count == 0,
        )


def collect_final_file_paths_from_yt_dlp_info(yt_dlp_info_dict: dict[str, Any]) -> Iterator[str]:
    # PROVENANCE: YoutubeDL.process_info stores the post-merge/post-move path in
    # requested_downloads[*].filepath; playlists nest the same structure under entries.
    requested_downloads: list[dict[str, Any]] = yt_dlp_info_dict.get("requested_downloads") or []
    for requested_download in requested_downloads:
        if requested_download.get("filepath"):
            yield requested_download["filepath"]
    playlist_entries: list[dict[str, Any] | None] = yt_dlp_info_dict.get("entries") or []
    for playlist_entry in playlist_entries:
        if playlist_entry:
            yield from collect_final_file_paths_from_yt_dlp_info(playlist_entry)


def iterate_yt_dlp_error_chain(yt_dlp_error: BaseException) -> Iterator[BaseException]:
    visited_error_identities: set[int] = set()
    current_error: BaseException | None = yt_dlp_error
    while current_error is not None and id(current_error) not in visited_error_identities:
        yield current_error
        visited_error_identities.add(id(current_error))
        unwrapped_error = (
            unwrap_original_yt_dlp_error_cause(current_error)
            if isinstance(current_error, Exception)
            else current_error
        )
        # PROVENANCE: OSError during a download is re-raised as UnavailableVideoError inside the
        # `except OSError` block (YoutubeDL.process_info), so it survives only as __context__.
        current_error = (
            unwrapped_error
            if unwrapped_error is not current_error
            else current_error.__cause__ or current_error.__context__
        )


def classify_yt_dlp_download_error(yt_dlp_error: BaseException) -> MediaDownloadFailureKind:
    for chained_error in iterate_yt_dlp_error_chain(yt_dlp_error):
        chained_failure_kind = classify_single_download_error(chained_error)
        if chained_failure_kind is not None:
            return chained_failure_kind
    return MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE


def classify_single_download_error(chained_error: BaseException) -> MediaDownloadFailureKind | None:
    if isinstance(chained_error, PostProcessingError):
        return MediaDownloadFailureKind.POSTPROCESSING_FAILED
    if isinstance(chained_error, HTTPError):
        if chained_error.status in TRANSIENT_HTTP_STATUS_CODES:
            return MediaDownloadFailureKind.NETWORK_UNREACHABLE
        return MediaDownloadFailureKind.MEDIA_UNAVAILABLE
    if isinstance(chained_error, TransportError):
        return MediaDownloadFailureKind.NETWORK_UNREACHABLE
    if isinstance(chained_error, OSError) and chained_error.errno is not None:
        return DOWNLOAD_FAILURE_KINDS_BY_OS_ERRNO.get(chained_error.errno)
    return None
