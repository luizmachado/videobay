import pytest

from videobay_gui.core.media_url_syntax_validation import (
    MediaUrlRejectionReason,
    describe_media_url_rejection_reason_for_user,
    validate_media_url_syntax,
)


@pytest.mark.parametrize(
    "raw_media_url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "http://vimeo.com/123456",
        "HTTPS://Example.com/video",
    ],
)
def test_accepts_http_and_https_urls_with_host(raw_media_url: str):
    media_url_validation_outcome = validate_media_url_syntax(raw_media_url)

    assert media_url_validation_outcome.is_media_url_acceptable
    assert media_url_validation_outcome.media_url_rejection_reason is None
    assert media_url_validation_outcome.normalized_media_url == raw_media_url


def test_strips_surrounding_whitespace_pasted_with_the_url():
    media_url_validation_outcome = validate_media_url_syntax("  https://youtu.be/abc \n")

    assert media_url_validation_outcome.is_media_url_acceptable
    assert media_url_validation_outcome.normalized_media_url == "https://youtu.be/abc"


@pytest.mark.parametrize(
    ("raw_media_url", "expected_media_url_rejection_reason"),
    [
        ("", MediaUrlRejectionReason.EMPTY_MEDIA_URL),
        ("   \t", MediaUrlRejectionReason.EMPTY_MEDIA_URL),
        ("youtube.com/watch?v=abc", MediaUrlRejectionReason.MISSING_URL_SCHEME),
        ("ftp://example.com/video.mp4", MediaUrlRejectionReason.UNSUPPORTED_URL_SCHEME),
        ("file:///home/user/video.mp4", MediaUrlRejectionReason.UNSUPPORTED_URL_SCHEME),
        ("https://", MediaUrlRejectionReason.MISSING_URL_HOST),
        ("https:///watch?v=abc", MediaUrlRejectionReason.MISSING_URL_HOST),
        ("https://exa mple.com/v", MediaUrlRejectionReason.WHITESPACE_INSIDE_URL),
    ],
)
def test_ec01_rejects_malformed_urls_with_specific_reason(
    raw_media_url: str, expected_media_url_rejection_reason: MediaUrlRejectionReason
):
    media_url_validation_outcome = validate_media_url_syntax(raw_media_url)

    assert not media_url_validation_outcome.is_media_url_acceptable
    assert (
        media_url_validation_outcome.media_url_rejection_reason
        == expected_media_url_rejection_reason
    )


@pytest.mark.parametrize("media_url_rejection_reason", list(MediaUrlRejectionReason))
def test_every_rejection_reason_has_a_non_empty_user_message(
    media_url_rejection_reason: MediaUrlRejectionReason,
):
    assert describe_media_url_rejection_reason_for_user(media_url_rejection_reason).strip()
