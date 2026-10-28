from dataclasses import dataclass

from videobay_gui.core.media_quality_choice import MediaQualityChoice


@dataclass(frozen=True)
class VideoDownloadRequest:
    media_url: str
    media_quality_choice: MediaQualityChoice
    output_directory: str
    is_playlist_download: bool = False
    # WHY: empty means "every item" for a playlist; ignored for single videos.
    selected_playlist_item_indices: tuple[int, ...] = ()
    selected_subtitle_languages: tuple[str, ...] = ()
