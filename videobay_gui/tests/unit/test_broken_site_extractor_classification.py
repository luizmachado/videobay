import pytest
from yt_dlp.utils import ExtractorError

from tests.unit.test_yt_dlp_metadata_extractor_adapter import wrap_like_youtube_dl_extract_info
from videobay_gui.adapters.yt_dlp_download_executor_adapter import classify_yt_dlp_download_error
from videobay_gui.adapters.yt_dlp_metadata_extractor_adapter import (
    classify_yt_dlp_inspection_error,
)
from videobay_gui.core.media_download_failure import (
    MediaDownloadFailureKind,
    describe_media_download_failure_for_user,
    is_media_download_failure_retryable,
)
from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailureKind,
    describe_media_inspection_failure_for_user,
    is_media_inspection_failure_retryable,
)


@pytest.mark.parametrize(
    "unexpected_extractor_error",
    [
        ExtractorError("Unable to extract initial player response"),
        wrap_like_youtube_dl_extract_info(ExtractorError("Unable to extract nsig function")),
    ],
)
def test_ec18_unexpected_extractor_errors_mean_the_site_changed(
    unexpected_extractor_error: Exception,
):
    assert classify_yt_dlp_inspection_error(unexpected_extractor_error) == (
        MediaInspectionFailureKind.BROKEN_SITE_EXTRACTOR
    )
    assert classify_yt_dlp_download_error(unexpected_extractor_error) == (
        MediaDownloadFailureKind.BROKEN_SITE_EXTRACTOR
    )


def test_expected_extractor_errors_keep_their_own_meaning():
    assert (
        classify_yt_dlp_inspection_error(ExtractorError("Video unavailable", expected=True))
        == MediaInspectionFailureKind.MEDIA_UNAVAILABLE
    )
    assert (
        classify_yt_dlp_inspection_error(
            ExtractorError("Something the site told us", expected=True)
        )
        == MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE
    )


def test_ec18_message_tells_the_user_to_sync_the_fork_and_offers_no_retry():
    inspection_message = describe_media_inspection_failure_for_user(
        MediaInspectionFailureKind.BROKEN_SITE_EXTRACTOR
    )
    download_message = describe_media_download_failure_for_user(
        MediaDownloadFailureKind.BROKEN_SITE_EXTRACTOR
    )

    assert "sincronize" in inspection_message.lower()
    assert "sincronize" in download_message.lower()
    assert not is_media_inspection_failure_retryable(
        MediaInspectionFailureKind.BROKEN_SITE_EXTRACTOR
    )
    assert not is_media_download_failure_retryable(MediaDownloadFailureKind.BROKEN_SITE_EXTRACTOR)
