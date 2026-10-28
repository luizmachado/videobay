from dataclasses import dataclass

from videobay_gui.core.media_quality_choice import MediaQualityChoice


@dataclass(frozen=True)
class VideoDownloadRequest:
    media_url: str
    media_quality_choice: MediaQualityChoice
    output_directory: str
