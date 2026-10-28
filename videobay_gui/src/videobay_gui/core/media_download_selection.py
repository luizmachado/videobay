from dataclasses import dataclass

from videobay_gui.core.media_quality_choice import MediaQualityChoice


@dataclass(frozen=True)
class MediaDownloadSelection:
    """What the inspection card currently offers for download."""

    media_url: str
    media_quality_choice: MediaQualityChoice
    media_display_title: str
    is_playlist_selection: bool = False
    selected_playlist_item_indices_for_download: tuple[int, ...] = ()
