import pytest

from videobay_gui.core.media_download_failure import (
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
    describe_media_download_failure_for_user,
    is_media_download_failure_retryable,
)


@pytest.mark.parametrize("media_download_failure_kind", list(MediaDownloadFailureKind))
def test_every_download_failure_kind_has_a_user_message(
    media_download_failure_kind: MediaDownloadFailureKind,
):
    assert describe_media_download_failure_for_user(media_download_failure_kind).strip()


@pytest.mark.parametrize(
    ("media_download_failure_kind", "expected_retryable"),
    [
        (MediaDownloadFailureKind.NETWORK_UNREACHABLE, True),
        (MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE, True),
        (MediaDownloadFailureKind.OUTPUT_DISK_FULL, True),
        (MediaDownloadFailureKind.MEDIA_UNAVAILABLE, False),
        (MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE, False),
        (MediaDownloadFailureKind.POSTPROCESSING_FAILED, False),
    ],
)
def test_retry_is_offered_only_when_a_new_attempt_can_succeed(
    media_download_failure_kind: MediaDownloadFailureKind, expected_retryable: bool
):
    assert is_media_download_failure_retryable(media_download_failure_kind) is expected_retryable


def test_download_failed_error_keeps_kind_and_detail():
    media_download_failed_error = MediaDownloadFailedError(
        MediaDownloadFailureKind.OUTPUT_DISK_FULL, "[Errno 28] No space left on device"
    )

    assert media_download_failed_error.media_download_failure_kind == (
        MediaDownloadFailureKind.OUTPUT_DISK_FULL
    )
    assert "No space" in str(media_download_failed_error)
