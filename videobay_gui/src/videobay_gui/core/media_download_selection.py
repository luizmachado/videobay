from dataclasses import dataclass

from videobay_gui.core.media_quality_choice import MediaQualityChoice


@dataclass(frozen=True)
class MediaDownloadSelection:
    """What the inspection card currently offers for download."""

    media_url: str
    media_quality_choice: MediaQualityChoice
    media_display_title: str
