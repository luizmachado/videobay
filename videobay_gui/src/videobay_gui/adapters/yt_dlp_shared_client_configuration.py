from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Protocol, cast

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError

# WHY: 429 (rate limit) and 5xx are transient, so the user gets "tentar de novo" for them.
TRANSIENT_HTTP_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


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


def build_yt_dlp_javascript_runtime_params(deno_executable_path: str | None) -> dict[str, Any]:
    if deno_executable_path is None:
        return {}
    # PROVENANCE: ADR-0008. YouTube needs a JS runtime for its challenges; without a path
    # yt-dlp keeps its default lookup (deno on PATH) and may return fewer formats.
    return {"js_runtimes": {"deno": {"path": deno_executable_path}}}


def unwrap_original_yt_dlp_error_cause(yt_dlp_error: Exception) -> Exception:
    # PROVENANCE: YoutubeDL.trouble() re-raises extraction failures as DownloadError and keeps
    # the original exception in exc_info (yt_dlp/YoutubeDL.py, `raise DownloadError(...)`).
    if not isinstance(yt_dlp_error, DownloadError) or not yt_dlp_error.exc_info:
        return yt_dlp_error
    original_yt_dlp_error = yt_dlp_error.exc_info[1]
    return original_yt_dlp_error if isinstance(original_yt_dlp_error, Exception) else yt_dlp_error


def is_broken_site_extractor_error(original_yt_dlp_error: BaseException) -> bool:
    # PROVENANCE: EC-18. ExtractorError(expected=False) is yt-dlp's "this is a bug" marker; it
    # also appends "please report this issue" to the message (utils/_utils.py, ExtractorError).
    if isinstance(original_yt_dlp_error, ExtractorError):
        return not original_yt_dlp_error.expected
    return "please report this issue" in str(original_yt_dlp_error).lower()
