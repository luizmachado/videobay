from typing import Protocol


class ThumbnailImageFetcherPort(Protocol):
    def fetch_thumbnail_image_bytes(self, thumbnail_url: str) -> bytes:
        """Blocking call. Raises ThumbnailImageFetchFailedError on any failure."""
        ...
