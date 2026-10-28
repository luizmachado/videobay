from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Protocol, cast

import yt_dlp
from yt_dlp.networking.exceptions import HTTPError, TransportError
from yt_dlp.utils import DownloadError, GeoRestrictedError, UnsupportedError, YoutubeDLError

from videobay_gui.core.inspected_media_summary import InspectedMediaSummary
from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailedError,
    MediaInspectionFailureKind,
)

# WHY: without a timeout a dead connection freezes the inspection worker forever (EC-03).
YT_DLP_INSPECTION_SOCKET_TIMEOUT_SECONDS = 15
# WHY: 429 (rate limit) and 5xx are transient, so the user gets "tentar de novo" for them.
TRANSIENT_HTTP_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
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


class YtDlpInfoExtractingClient(Protocol):
    def extract_info(self, url: str, download: bool = True) -> dict[str, Any] | None: ...


type YtDlpInfoExtractingClientFactory = Callable[
    [dict[str, Any]], AbstractContextManager[YtDlpInfoExtractingClient]
]


def build_real_yt_dlp_info_extracting_client(
    yt_dlp_params: dict[str, Any],
) -> AbstractContextManager[YtDlpInfoExtractingClient]:
    # WHY: yt_dlp types params as a private TypedDict and extract_info loosely; casting only
    # here keeps the rest of the adapter strictly typed.
    real_yt_dlp_client = yt_dlp.YoutubeDL(cast(Any, yt_dlp_params))
    return cast(AbstractContextManager[YtDlpInfoExtractingClient], real_yt_dlp_client)


class SilencedYtDlpLoggerForGui:
    """yt-dlp writes errors to stderr by default; the GUI reports them via exceptions instead."""

    def debug(self, yt_dlp_log_message: str) -> None:
        return None

    def info(self, yt_dlp_log_message: str) -> None:
        return None

    def warning(self, yt_dlp_log_message: str) -> None:
        return None

    def error(self, yt_dlp_log_message: str) -> None:
        return None


def build_yt_dlp_media_inspection_params() -> dict[str, Any]:
    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # WHY: flat playlist listing keeps huge playlists fast to inspect (EC-12).
        "extract_flat": "in_playlist",
        "socket_timeout": YT_DLP_INSPECTION_SOCKET_TIMEOUT_SECONDS,
        "logger": SilencedYtDlpLoggerForGui(),
    }


class YtDlpMetadataExtractorAdapter:
    def __init__(
        self,
        yt_dlp_client_factory: YtDlpInfoExtractingClientFactory = (
            build_real_yt_dlp_info_extracting_client
        ),
    ) -> None:
        self.yt_dlp_client_factory = yt_dlp_client_factory

    def extract_inspected_media_summary(self, media_url: str) -> InspectedMediaSummary:
        try:
            with self.yt_dlp_client_factory(
                build_yt_dlp_media_inspection_params()
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
    )


def pick_best_yt_dlp_thumbnail_url(yt_dlp_info_dict: dict[str, Any]) -> str | None:
    if yt_dlp_info_dict.get("thumbnail"):
        return yt_dlp_info_dict["thumbnail"]
    # PROVENANCE: yt-dlp sorts `thumbnails` from worst to best, so the last entry is the largest.
    yt_dlp_thumbnail_entries: list[dict[str, Any]] = yt_dlp_info_dict.get("thumbnails") or []
    if not yt_dlp_thumbnail_entries:
        return None
    return yt_dlp_thumbnail_entries[-1].get("url")


def unwrap_original_yt_dlp_error_cause(yt_dlp_error: Exception) -> Exception:
    # PROVENANCE: YoutubeDL.trouble() re-raises extraction failures as DownloadError and keeps
    # the original exception in exc_info (yt_dlp/YoutubeDL.py, `raise DownloadError(...)`).
    if not isinstance(yt_dlp_error, DownloadError) or not yt_dlp_error.exc_info:
        return yt_dlp_error
    original_yt_dlp_error = yt_dlp_error.exc_info[1]
    return original_yt_dlp_error if isinstance(original_yt_dlp_error, Exception) else yt_dlp_error


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
