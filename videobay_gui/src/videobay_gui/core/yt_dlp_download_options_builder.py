import os
from dataclasses import dataclass
from typing import Any

from videobay_gui.core.media_quality_choice import AudioOutputCodec, MediaQualityChoice
from videobay_gui.core.video_download_request import VideoDownloadRequest

FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE = (
    "ffmpeg não encontrado: baixando o melhor arquivo único disponível, que pode ter "
    "qualidade menor. Instale o ffmpeg para ter a melhor qualidade."
)
FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE = (
    "Para extrair o áudio é preciso o ffmpeg. Instale com `sudo apt install ffmpeg` "
    "e tente de novo."
)
# PROVENANCE: yt-dlp's --audio-quality 0 = best VBR for mp3; for m4a it keeps the source AAC
# when possible instead of re-encoding.
BEST_AUDIO_EXTRACTION_QUALITY = "0"
# WHY: the id makes names unique when two videos share a title, and keeps re-downloads
# detectable by yt-dlp's no-overwrite check (EC-07).
# WHY: the real height keeps "Melhor" and "Até 144p" of the same video from colliding on one
# file name (found in the S-017 end-to-end check, where the second was wrongly "Já baixado").
# PROVENANCE: yt-dlp output-template replacement syntax `%(field&replacement|default)s`;
# audio-only downloads have no height, so they get no suffix.
VIDEOBAY_OUTPUT_FILENAME_TEMPLATE = "%(title)s [%(id)s]%(height& {}p|)s.%(ext)s"
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
        "outtmpl": {"default": build_output_path_template(video_download_request)},
        "overwrites": False,
        **build_yt_dlp_playlist_scope_options(video_download_request),
        **build_yt_dlp_subtitle_options(video_download_request.selected_subtitle_languages),
    }
    audio_output_codec = video_download_request.media_quality_choice.audio_output_codec
    if audio_output_codec is not None:
        yt_dlp_download_options["postprocessors"] = [
            build_audio_extraction_postprocessor(audio_output_codec)
        ]
        return YtDlpDownloadOptionsBuildResult(yt_dlp_download_options, None)
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


def build_audio_extraction_postprocessor(audio_output_codec: AudioOutputCodec) -> dict[str, str]:
    return {
        "key": "FFmpegExtractAudio",
        "preferredcodec": audio_output_codec.value,
        "preferredquality": BEST_AUDIO_EXTRACTION_QUALITY,
    }


def find_download_blocking_problem(
    video_download_request: VideoDownloadRequest, is_ffmpeg_available: bool
) -> str | None:
    # WHY: EC-05. Unlike video (EC-04) there is no ffmpeg-free fallback that still delivers
    # the MP3/M4A the user asked for, so the download is blocked with an install instruction.
    if video_download_request.media_quality_choice.is_audio_only and not is_ffmpeg_available:
        return FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE
    return None


def build_yt_dlp_subtitle_options(selected_subtitle_languages: tuple[str, ...]) -> dict[str, Any]:
    if not selected_subtitle_languages:
        return {}
    # WHY: side files (.srt preferred, else .vtt) need no ffmpeg, unlike embedding.
    return {
        "writesubtitles": True,
        "subtitleslangs": list(selected_subtitle_languages),
        "subtitlesformat": "srt/vtt/best",
    }


def build_output_path_template(video_download_request: VideoDownloadRequest) -> str:
    if not video_download_request.is_playlist_download:
        return os.path.join(
            video_download_request.output_directory, VIDEOBAY_OUTPUT_FILENAME_TEMPLATE
        )
    # WHY: one folder per playlist, numbered like the playlist, keeps a 96-video course from
    # flooding the download folder and preserves the intended order.
    return os.path.join(
        video_download_request.output_directory,
        "%(playlist_title)s",
        "%(playlist_index)s - " + VIDEOBAY_OUTPUT_FILENAME_TEMPLATE,
    )


def build_yt_dlp_playlist_scope_options(
    video_download_request: VideoDownloadRequest,
) -> dict[str, Any]:
    if not video_download_request.is_playlist_download:
        # WHY: a "watch?v=…&list=…" URL inspected as a single video must not pull the list.
        return {"noplaylist": True}
    # WHY: EC-11. One private or deleted item must not abort the rest of the playlist.
    playlist_scope_options: dict[str, Any] = {"ignoreerrors": True}
    if video_download_request.selected_playlist_item_indices:
        playlist_scope_options["playlist_items"] = compress_playlist_item_indices_to_yt_dlp_ranges(
            video_download_request.selected_playlist_item_indices
        )
    return playlist_scope_options


def compress_playlist_item_indices_to_yt_dlp_ranges(playlist_item_indices: tuple[int, ...]) -> str:
    sorted_unique_indices = sorted(set(playlist_item_indices))
    index_ranges: list[tuple[int, int]] = []
    for playlist_item_index in sorted_unique_indices:
        if index_ranges and playlist_item_index == index_ranges[-1][1] + 1:
            index_ranges[-1] = (index_ranges[-1][0], playlist_item_index)
            continue
        index_ranges.append((playlist_item_index, playlist_item_index))
    # PROVENANCE: yt-dlp --playlist-items syntax, e.g. "1-3,7,9-10" (1-based, inclusive).
    return ",".join(
        str(range_start) if range_start == range_end else f"{range_start}-{range_end}"
        for range_start, range_end in index_ranges
    )
