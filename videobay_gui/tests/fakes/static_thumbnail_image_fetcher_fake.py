from videobay_gui.core.thumbnail_image_fetch_failure import ThumbnailImageFetchFailedError


class StaticThumbnailImageFetcherFake:
    """Returns fixed bytes per thumbnail URL; unknown URLs fail like an unreachable server."""

    def __init__(self) -> None:
        self.thumbnail_image_bytes_by_url: dict[str, bytes] = {}
        self.fetched_thumbnail_urls: list[str] = []

    def script_thumbnail_image_bytes(self, thumbnail_url: str, thumbnail_bytes: bytes) -> None:
        self.thumbnail_image_bytes_by_url[thumbnail_url] = thumbnail_bytes

    def fetch_thumbnail_image_bytes(self, thumbnail_url: str) -> bytes:
        self.fetched_thumbnail_urls.append(thumbnail_url)
        if thumbnail_url not in self.thumbnail_image_bytes_by_url:
            raise ThumbnailImageFetchFailedError(f"no scripted thumbnail for {thumbnail_url}")
        return self.thumbnail_image_bytes_by_url[thumbnail_url]
