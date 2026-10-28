import io
import sys
from types import TracebackType
from typing import Any

import pytest
from yt_dlp.networking.common import Response
from yt_dlp.networking.exceptions import HTTPError, TransportError
from yt_dlp.utils import DownloadError, ExtractorError, GeoRestrictedError, UnsupportedError

from tests.fakes.scripted_yt_dlp_info_extracting_client_fake import (
    ScriptedYtDlpInfoExtractingClientFake,
)
from videobay_gui.adapters.yt_dlp_metadata_extractor_adapter import (
    YtDlpMetadataExtractorAdapter,
    classify_yt_dlp_inspection_error,
)
from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailedError,
    MediaInspectionFailureKind,
)

SAMPLE_VIDEO_URL = "https://www.youtube.com/watch?v=BaW_jenozKc"
TRUNCATED_SAMPLE_DURATION_SECONDS = 10


def wrap_like_youtube_dl_extract_info(original_yt_dlp_error: Exception) -> DownloadError:
    """Mimics YoutubeDL.trouble(): the DownloadError keeps the original error in exc_info."""
    try:
        raise original_yt_dlp_error
    except Exception:
        captured_exc_info: tuple[type[BaseException], BaseException, TracebackType] = sys.exc_info()  # type: ignore[assignment]
    return DownloadError(f"ERROR: {original_yt_dlp_error}", captured_exc_info)


def build_yt_dlp_http_error(http_status_code: int) -> HTTPError:
    return HTTPError(Response(io.BytesIO(b""), SAMPLE_VIDEO_URL, {}, status=http_status_code))


@pytest.mark.parametrize(
    ("raised_yt_dlp_error", "expected_media_inspection_failure_kind"),
    [
        (GeoRestrictedError("blocked"), MediaInspectionFailureKind.GEO_RESTRICTED),
        (UnsupportedError("https://example.com"), MediaInspectionFailureKind.UNSUPPORTED_SITE),
        (TransportError("timed out"), MediaInspectionFailureKind.NETWORK_UNREACHABLE),
        (build_yt_dlp_http_error(503), MediaInspectionFailureKind.NETWORK_UNREACHABLE),
        (build_yt_dlp_http_error(429), MediaInspectionFailureKind.NETWORK_UNREACHABLE),
        (build_yt_dlp_http_error(404), MediaInspectionFailureKind.MEDIA_UNAVAILABLE),
        (
            ExtractorError("Sign in to confirm your age. This video may be inappropriate"),
            MediaInspectionFailureKind.AGE_RESTRICTED,
        ),
        (ExtractorError("Private video. Sign in"), MediaInspectionFailureKind.MEDIA_UNAVAILABLE),
        (ExtractorError("Video unavailable"), MediaInspectionFailureKind.MEDIA_UNAVAILABLE),
        (
            ExtractorError("[vimeo] 76979871: The web client only works when logged-in."),
            MediaInspectionFailureKind.MEDIA_UNAVAILABLE,
        ),
        (
            ExtractorError("This video has been removed by the uploader"),
            MediaInspectionFailureKind.MEDIA_UNAVAILABLE,
        ),
        (
            ExtractorError("Unable to extract title"),
            MediaInspectionFailureKind.BROKEN_SITE_EXTRACTOR,
        ),
    ],
)
def test_ec02_ec03_classifies_wrapped_and_bare_yt_dlp_errors(
    raised_yt_dlp_error: Exception,
    expected_media_inspection_failure_kind: MediaInspectionFailureKind,
):
    assert classify_yt_dlp_inspection_error(raised_yt_dlp_error) == (
        expected_media_inspection_failure_kind
    )
    assert (
        classify_yt_dlp_inspection_error(wrap_like_youtube_dl_extract_info(raised_yt_dlp_error))
        == expected_media_inspection_failure_kind
    )


def test_download_error_without_cause_falls_back_to_its_message():
    assert (
        classify_yt_dlp_inspection_error(DownloadError("ERROR: [youtube] abc: Video unavailable"))
        == MediaInspectionFailureKind.MEDIA_UNAVAILABLE
    )


def build_adapter_with_scripted_client(
    scripted_info_dict: dict[str, Any] | None = None,
    scripted_extraction_error: Exception | None = None,
) -> tuple[YtDlpMetadataExtractorAdapter, ScriptedYtDlpInfoExtractingClientFake]:
    scripted_client = ScriptedYtDlpInfoExtractingClientFake(
        scripted_info_dict, scripted_extraction_error
    )
    return YtDlpMetadataExtractorAdapter(scripted_client.build_from_yt_dlp_params), scripted_client


def test_maps_video_info_dict_to_inspected_summary():
    adapter, _ = build_adapter_with_scripted_client(
        {
            "title": "youtube-dl test video",
            "uploader": "Philipp Hagemeister",
            "duration": 10.4,
            "thumbnail": "https://i.ytimg.com/vi/BaW_jenozKc/maxresdefault.jpg",
            "live_status": "not_live",
        }
    )

    inspected_media_summary = adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    assert inspected_media_summary.media_url == SAMPLE_VIDEO_URL
    assert inspected_media_summary.media_title == "youtube-dl test video"
    assert inspected_media_summary.media_uploader_name == "Philipp Hagemeister"
    assert inspected_media_summary.media_duration_seconds == TRUNCATED_SAMPLE_DURATION_SECONDS
    assert inspected_media_summary.media_thumbnail_url is not None
    assert inspected_media_summary.is_live_broadcast is False


@pytest.mark.parametrize(
    ("live_info_fields", "expected_is_live_broadcast"),
    [
        ({"is_live": True}, True),
        ({"live_status": "is_live"}, True),
        ({"live_status": "is_upcoming"}, True),
        ({"live_status": "was_live"}, False),
        ({}, False),
    ],
)
def test_ec17_detects_live_and_upcoming_broadcasts(
    live_info_fields: dict[str, Any], expected_is_live_broadcast: bool
):
    adapter, _ = build_adapter_with_scripted_client({"title": "x", **live_info_fields})

    assert adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL).is_live_broadcast is (
        expected_is_live_broadcast
    )


def test_falls_back_to_channel_and_last_thumbnail_when_primary_fields_missing():
    adapter, _ = build_adapter_with_scripted_client(
        {
            "title": "x",
            "channel": "Canal Alternativo",
            "thumbnails": [{"url": "https://t/low.jpg"}, {"url": "https://t/high.jpg"}],
        }
    )

    inspected_media_summary = adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    assert inspected_media_summary.media_uploader_name == "Canal Alternativo"
    assert inspected_media_summary.media_thumbnail_url == "https://t/high.jpg"
    assert inspected_media_summary.media_duration_seconds is None


def test_passes_quiet_flat_timeout_params_and_never_downloads():
    adapter, scripted_client = build_adapter_with_scripted_client({"title": "x"})

    adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    received_params = scripted_client.received_yt_dlp_params
    assert received_params["quiet"] is True
    assert received_params["skip_download"] is True
    assert received_params["extract_flat"] == "in_playlist"
    assert received_params["socket_timeout"] > 0
    assert received_params["logger"] is not None
    assert scripted_client.received_extract_info_calls == [(SAMPLE_VIDEO_URL, False)]


def test_ec02_wraps_yt_dlp_errors_into_media_inspection_failed_error():
    adapter, _ = build_adapter_with_scripted_client(
        scripted_extraction_error=wrap_like_youtube_dl_extract_info(GeoRestrictedError("no"))
    )

    with pytest.raises(MediaInspectionFailedError) as raised_failure:
        adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    assert raised_failure.value.media_inspection_failure_kind == (
        MediaInspectionFailureKind.GEO_RESTRICTED
    )


def test_missing_info_dict_is_an_unknown_extraction_failure():
    adapter, _ = build_adapter_with_scripted_client(None)

    with pytest.raises(MediaInspectionFailedError) as raised_failure:
        adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    assert raised_failure.value.media_inspection_failure_kind == (
        MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE
    )


def test_collects_heights_only_from_formats_that_carry_video():
    adapter, _ = build_adapter_with_scripted_client(
        {
            "title": "x",
            "formats": [
                {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "height": None},
                {"format_id": "137", "vcodec": "avc1", "height": 1080},
                {"format_id": "136", "vcodec": "avc1", "height": 720},
                {"format_id": "sb0", "vcodec": "none", "height": 90},
                {"format_id": "hls", "height": 480},
                {"format_id": "odd"},
            ],
        }
    )

    inspected_media_summary = adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    assert sorted(inspected_media_summary.available_video_heights) == [480, 720, 1080]


def test_passes_bundled_deno_path_to_yt_dlp_javascript_runtimes():
    scripted_client = ScriptedYtDlpInfoExtractingClientFake({"title": "x"})
    adapter = YtDlpMetadataExtractorAdapter(
        scripted_client.build_from_yt_dlp_params, deno_executable_path="/bundle/deno"
    )

    adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    assert scripted_client.received_yt_dlp_params["js_runtimes"] == {
        "deno": {"path": "/bundle/deno"}
    }


def test_leaves_yt_dlp_default_runtime_lookup_when_no_deno_path_is_known():
    adapter, scripted_client = build_adapter_with_scripted_client({"title": "x"})

    adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    assert "js_runtimes" not in scripted_client.received_yt_dlp_params
