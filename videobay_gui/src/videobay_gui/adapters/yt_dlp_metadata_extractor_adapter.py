from typing import Any

from yt_dlp.networking.exceptions import HTTPError, TransportError
from yt_dlp.utils import GeoRestrictedError, UnsupportedError, YoutubeDLError

from videobay_gui.adapters.yt_dlp_shared_client_configuration import (
    TRANSIENT_HTTP_STATUS_CODES,
    SilencedYtDlpLoggerForGui,
    YtDlpInfoExtractingClientFactory,
    build_real_yt_dlp_info_extracting_client,
    build_yt_dlp_javascript_runtime_params,
    unwrap_original_yt_dlp_error_cause,
)
from videobay_gui.core.inspected_media_summary import InspectedMediaSummary
from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailedError,
    MediaInspectionFailureKind,
)

# WHY: without a timeout a dead connection freezes the inspection worker forever (EC-03).
YT_DLP_INSPECTION_SOCKET_TIMEOUT_SECONDS = 15
LIVE_OR_UPCOMING_YT_DLP_LIVE_STATUSES = frozenset({"is_live", "is_upcoming"})
# PROVENANCE: substrings of yt-dlp extractor messages (youtube/_video.py, common.py login
# helpers); yt-dlp raises plain ExtractorError for these, so the text is the only signal.
AGE_RESTRICTION_MESSAGE_FRAGMENTS = ("confirm your age", "age-restricted", "age restricted")
MEDIA_UNAVAILABLE_MESSAGE_FRAGMENTS = (
    "private video",
    "video unavailable",
    "has been removed",
    "members-only",
    "sign in",
    "login required",
    "logged-in",
    "not available",
)


def build_yt_dlp_media_inspection_params(deno_executable_path: str | None) -> dict[str, Any]:
    yt_dlp_media_inspection_params: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # WHY: flat playlist listing keeps huge playlists fast to inspect (EC-12).
        "extract_flat": "in_playlist",
        "socket_timeout": YT_DLP_INSPECTION_SOCKET_TIMEOUT_SECONDS,
        "logger": SilencedYtDlpLoggerForGui(),
    }
    yt_dlp_media_inspection_params.update(
        build_yt_dlp_javascript_runtime_params(deno_executable_path)
    )
    return yt_dlp_media_inspection_params


class YtDlpMetadataExtractorAdapter:
    def __init__(
        self,
        yt_dlp_client_factory: YtDlpInfoExtractingClientFactory = (
            build_real_yt_dlp_info_extracting_client
        ),
        deno_executable_path: str | None = None,
    ) -> None:
        self.yt_dlp_client_factory = yt_dlp_client_factory
        self.deno_executable_path = deno_executable_path

    def extract_inspected_media_summary(self, media_url: str) -> InspectedMediaSummary:
        try:
            with self.yt_dlp_client_factory(
                build_yt_dlp_media_inspection_params(self.deno_executable_path)
            ) as yt_dlp_client:
                yt_dlp_info_dict = yt_dlp_client.extract_info(media_url, download=False)
        except YoutubeDLError as yt_dlp_error:
            raise MediaInspectionFailedError(
                classify_yt_dlp_inspection_error(yt_dlp_error), str(yt_dlp_error)
            ) from yt_dlp_error
        if yt_dlp_info_dict is None:
            raise MediaInspectionFailedError(
                MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE, "yt-dlp returned no info"
            )
        return build_inspected_media_summary_from_yt_dlp_info_dict(media_url, yt_dlp_info_dict)


def build_inspected_media_summary_from_yt_dlp_info_dict(
    media_url: str, yt_dlp_info_dict: dict[str, Any]
) -> InspectedMediaSummary:
    yt_dlp_duration_seconds = yt_dlp_info_dict.get("duration")
    return InspectedMediaSummary(
        media_url=media_url,
        media_title=str(yt_dlp_info_dict.get("title") or ""),
        media_uploader_name=yt_dlp_info_dict.get("uploader") or yt_dlp_info_dict.get("channel"),
        media_duration_seconds=(
            int(yt_dlp_duration_seconds) if yt_dlp_duration_seconds is not None else None
        ),
        media_thumbnail_url=pick_best_yt_dlp_thumbnail_url(yt_dlp_info_dict),
        is_live_broadcast=bool(yt_dlp_info_dict.get("is_live"))
        or yt_dlp_info_dict.get("live_status") in LIVE_OR_UPCOMING_YT_DLP_LIVE_STATUSES,
        available_video_heights=collect_available_video_heights_from_yt_dlp_formats(
            yt_dlp_info_dict.get("formats") or []
        ),
    )


def collect_available_video_heights_from_yt_dlp_formats(
    yt_dlp_format_entries: list[dict[str, Any]],
) -> tuple[int, ...]:
    # WHY: audio-only formats and storyboard thumbnails ("sb*") report vcodec "none"; their
    # height must not create fake resolution options.
    return tuple(
        yt_dlp_format_entry["height"]
        for yt_dlp_format_entry in yt_dlp_format_entries
        if isinstance(yt_dlp_format_entry.get("height"), int)
        and yt_dlp_format_entry.get("vcodec") != "none"
    )


def pick_best_yt_dlp_thumbnail_url(yt_dlp_info_dict: dict[str, Any]) -> str | None:
    if yt_dlp_info_dict.get("thumbnail"):
        return yt_dlp_info_dict["thumbnail"]
    # PROVENANCE: yt-dlp sorts `thumbnails` from worst to best, so the last entry is the largest.
    yt_dlp_thumbnail_entries: list[dict[str, Any]] = yt_dlp_info_dict.get("thumbnails") or []
    if not yt_dlp_thumbnail_entries:
        return None
    return yt_dlp_thumbnail_entries[-1].get("url")


def classify_yt_dlp_inspection_error(yt_dlp_error: Exception) -> MediaInspectionFailureKind:
    original_yt_dlp_error = unwrap_original_yt_dlp_error_cause(yt_dlp_error)
    if isinstance(original_yt_dlp_error, GeoRestrictedError):
        return MediaInspectionFailureKind.GEO_RESTRICTED
    if isinstance(original_yt_dlp_error, UnsupportedError):
        return MediaInspectionFailureKind.UNSUPPORTED_SITE
    if isinstance(original_yt_dlp_error, HTTPError):
        return classify_yt_dlp_http_error_status(original_yt_dlp_error.status)
    if isinstance(original_yt_dlp_error, TransportError):
        return MediaInspectionFailureKind.NETWORK_UNREACHABLE
    return classify_yt_dlp_error_message(str(yt_dlp_error).lower())


def classify_yt_dlp_http_error_status(http_status_code: int) -> MediaInspectionFailureKind:
    if http_status_code in TRANSIENT_HTTP_STATUS_CODES:
        return MediaInspectionFailureKind.NETWORK_UNREACHABLE
    return MediaInspectionFailureKind.MEDIA_UNAVAILABLE


def classify_yt_dlp_error_message(
    lowercase_yt_dlp_error_message: str,
) -> MediaInspectionFailureKind:
    if any(
        age_fragment in lowercase_yt_dlp_error_message
        for age_fragment in AGE_RESTRICTION_MESSAGE_FRAGMENTS
    ):
        return MediaInspectionFailureKind.AGE_RESTRICTED
    if any(
        unavailable_fragment in lowercase_yt_dlp_error_message
        for unavailable_fragment in MEDIA_UNAVAILABLE_MESSAGE_FRAGMENTS
    ):
        return MediaInspectionFailureKind.MEDIA_UNAVAILABLE
    return MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE
