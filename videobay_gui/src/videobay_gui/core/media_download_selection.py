from dataclasses import dataclass

from videobay_gui.core.media_quality_choice import MediaQualityChoice
from videobay_gui.core.video_download_request import VideoDownloadRequest

NO_PLAYLIST_ITEMS_SELECTED_NOTICE = "Marque ao menos um vídeo da playlist."
PLAYLIST_SUBTITLES_MAY_BE_MISSING_NOTICE = (
    "Só os vídeos da playlist que tiverem o idioma escolhido receberão legendas."
)


@dataclass(frozen=True)
class MediaDownloadSelection:
    """What the inspection card currently offers for download."""

    media_url: str
    media_quality_choice: MediaQualityChoice
    media_display_title: str
    is_playlist_selection: bool = False
    selected_playlist_item_indices_for_download: tuple[int, ...] = ()
    selected_subtitle_languages: tuple[str, ...] = ()


def build_video_download_request_from_selection(
    media_download_selection: MediaDownloadSelection, output_directory: str
) -> VideoDownloadRequest:
    return VideoDownloadRequest(
        media_download_selection.media_url,
        media_download_selection.media_quality_choice,
        output_directory,
        is_playlist_download=media_download_selection.is_playlist_selection,
        selected_playlist_item_indices=(
            media_download_selection.selected_playlist_item_indices_for_download
        ),
        selected_subtitle_languages=media_download_selection.selected_subtitle_languages,
    )


def compose_enqueue_notice_for_selection(
    media_download_selection: MediaDownloadSelection, ffmpeg_fallback_notice: str | None
) -> str | None:
    enqueue_notices = [ffmpeg_fallback_notice] if ffmpeg_fallback_notice else []
    # WHY: EC-13. Playlists only offer common languages, so some items may have none.
    if media_download_selection.is_playlist_selection and (
        media_download_selection.selected_subtitle_languages
    ):
        enqueue_notices.append(PLAYLIST_SUBTITLES_MAY_BE_MISSING_NOTICE)
    return " ".join(enqueue_notices) or None


def find_playlist_selection_blocking_notice(
    media_download_selection: MediaDownloadSelection,
) -> str | None:
    # WHY: an empty item filter means "whole playlist" to yt-dlp; unchecking everything must
    # never turn into downloading everything.
    if media_download_selection.is_playlist_selection and not (
        media_download_selection.selected_playlist_item_indices_for_download
    ):
        return NO_PLAYLIST_ITEMS_SELECTED_NOTICE
    return None
