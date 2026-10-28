import os
from dataclasses import dataclass
from typing import Any

from videobay_gui.core.media_quality_choice import MediaQualityChoice
from videobay_gui.core.video_download_request import VideoDownloadRequest

FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE = (
    "ffmpeg não encontrado: baixando o melhor arquivo único disponível, que pode ter "
    "qualidade menor. Instale o ffmpeg para ter a melhor qualidade."
)
# WHY: the id makes names unique when two videos share a title, and keeps re-downloads
# detectable by yt-dlp's no-overwrite check (EC-07).
VIDEOBAY_OUTPUT_FILENAME_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
# PROVENANCE: yt-dlp accepts "a/b" here and picks the first container that fits the streams;
# mp4 plays everywhere, mkv takes codecs mp4 cannot hold (e.g. vp9 + opus on some sites).
VIDEOBAY_MERGE_OUTPUT_CONTAINERS = "mp4/mkv"


@dataclass(frozen=True)
class YtDlpDownloadOptionsBuildResult:
    yt_dlp_download_options: dict[str, Any]
    ffmpeg_fallback_notice: str | None


def build_yt_dlp_download_options(
    video_download_request: VideoDownloadRequest, is_ffmpeg_available: bool
) -> YtDlpDownloadOptionsBuildResult:
    yt_dlp_download_options: dict[str, Any] = {
        "format": build_yt_dlp_format_selector_for_quality(
            video_download_request.media_quality_choice, is_ffmpeg_available
        ),
        "outtmpl": {
            "default": os.path.join(
                video_download_request.output_directory, VIDEOBAY_OUTPUT_FILENAME_TEMPLATE
            )
        },
        "overwrites": False,
    }
    if not is_ffmpeg_available:
        return YtDlpDownloadOptionsBuildResult(
            yt_dlp_download_options, FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE
        )
    yt_dlp_download_options["merge_output_format"] = VIDEOBAY_MERGE_OUTPUT_CONTAINERS
    return YtDlpDownloadOptionsBuildResult(yt_dlp_download_options, None)


def build_yt_dlp_format_selector_for_quality(
    media_quality_choice: MediaQualityChoice, is_ffmpeg_available: bool
) -> str:
    if media_quality_choice.is_audio_only:
        return "ba/b"
    maximum_video_height = media_quality_choice.maximum_video_height
    if not is_ffmpeg_available:
        # WHY: without ffmpeg yt-dlp cannot merge separate video+audio streams (EC-04), so only
        # pre-merged single files ("b") are usable.
        return "b" if maximum_video_height is None else f"b[height<={maximum_video_height}]/b"
    if maximum_video_height is None:
        return "bv*+ba/b"
    return f"bv*[height<={maximum_video_height}]+ba/b[height<={maximum_video_height}]"
