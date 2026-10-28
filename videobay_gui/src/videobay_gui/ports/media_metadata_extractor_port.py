from typing import Protocol

from videobay_gui.core.inspected_media_summary import InspectedMediaSummary


class MediaMetadataExtractorPort(Protocol):
    def extract_inspected_media_summary(self, media_url: str) -> InspectedMediaSummary:
        """Blocking call. Raises MediaInspectionFailedError for every known yt-dlp failure."""
        ...
