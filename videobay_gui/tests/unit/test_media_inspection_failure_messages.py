import pytest

from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailedError,
    MediaInspectionFailureKind,
    describe_media_inspection_failure_for_user,
    is_media_inspection_failure_retryable,
)


@pytest.mark.parametrize("media_inspection_failure_kind", list(MediaInspectionFailureKind))
def test_every_failure_kind_has_a_non_empty_user_message(
    media_inspection_failure_kind: MediaInspectionFailureKind,
):
    assert describe_media_inspection_failure_for_user(media_inspection_failure_kind).strip()


@pytest.mark.parametrize(
    ("media_inspection_failure_kind", "expected_retryable"),
    [
        (MediaInspectionFailureKind.NETWORK_UNREACHABLE, True),
        (MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE, True),
        (MediaInspectionFailureKind.UNSUPPORTED_SITE, False),
        (MediaInspectionFailureKind.MEDIA_UNAVAILABLE, False),
        (MediaInspectionFailureKind.GEO_RESTRICTED, False),
        (MediaInspectionFailureKind.AGE_RESTRICTED, False),
        (MediaInspectionFailureKind.LIVE_BROADCAST_NOT_SUPPORTED, False),
    ],
)
def test_only_transient_failures_are_retryable(
    media_inspection_failure_kind: MediaInspectionFailureKind, expected_retryable: bool
):
    assert is_media_inspection_failure_retryable(media_inspection_failure_kind) is (
        expected_retryable
    )


def test_failed_error_keeps_kind_and_technical_detail_for_logs():
    media_inspection_failed_error = MediaInspectionFailedError(
        MediaInspectionFailureKind.GEO_RESTRICTED, "ERROR: [youtube] abc: blocked in BR"
    )

    assert media_inspection_failed_error.media_inspection_failure_kind == (
        MediaInspectionFailureKind.GEO_RESTRICTED
    )
    assert "blocked in BR" in str(media_inspection_failed_error)
