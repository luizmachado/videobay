import os

from videobay_gui.core.media_download_failure import (
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
    describe_media_download_failure_for_user,
    is_media_download_failure_retryable,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome


def describe_finished_download_outcome_for_job_row(
    media_download_outcome: MediaDownloadOutcome,
) -> str:
    downloaded_file_name = (
        os.path.basename(media_download_outcome.downloaded_file_paths[0])
        if media_download_outcome.downloaded_file_paths
        else ""
    )
    if media_download_outcome.was_already_downloaded:
        return f"Já baixado: {downloaded_file_name}"
    return downloaded_file_name


def describe_download_failure_for_job_row(media_download_error: Exception) -> tuple[str, bool]:
    """Returns the user message and whether "Tentar de novo" can help for this failure."""
    media_download_failure_kind = (
        media_download_error.media_download_failure_kind
        if isinstance(media_download_error, MediaDownloadFailedError)
        else MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE
    )
    return (
        describe_media_download_failure_for_user(media_download_failure_kind),
        is_media_download_failure_retryable(media_download_failure_kind),
    )
