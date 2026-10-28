import urllib.request

from videobay_gui import __version__
from videobay_gui.core.thumbnail_image_fetch_failure import ThumbnailImageFetchFailedError

DEFAULT_THUMBNAIL_FETCH_TIMEOUT_SECONDS = 10
# WHY: YouTube maxres thumbnails are ~200 KB; the cap stops a hostile URL from filling memory.
DEFAULT_MAXIMUM_THUMBNAIL_BYTE_COUNT = 5_000_000
# WHY: thumbnail URLs come from site metadata, so file:// or other schemes must never be opened.
ACCEPTED_THUMBNAIL_URL_PREFIXES = ("http://", "https://")


class UrllibThumbnailImageFetcherAdapter:
    def __init__(
        self,
        thumbnail_fetch_timeout_seconds: int = DEFAULT_THUMBNAIL_FETCH_TIMEOUT_SECONDS,
        maximum_thumbnail_byte_count: int = DEFAULT_MAXIMUM_THUMBNAIL_BYTE_COUNT,
    ) -> None:
        self.thumbnail_fetch_timeout_seconds = thumbnail_fetch_timeout_seconds
        self.maximum_thumbnail_byte_count = maximum_thumbnail_byte_count

    def fetch_thumbnail_image_bytes(self, thumbnail_url: str) -> bytes:
        if not thumbnail_url.lower().startswith(ACCEPTED_THUMBNAIL_URL_PREFIXES):
            raise ThumbnailImageFetchFailedError(
                f"unsupported thumbnail URL scheme: {thumbnail_url}"
            )
        thumbnail_request = urllib.request.Request(
            thumbnail_url, headers={"User-Agent": f"VideoBay/{__version__}"}
        )
        try:
            with urllib.request.urlopen(
                thumbnail_request, timeout=self.thumbnail_fetch_timeout_seconds
            ) as thumbnail_response:
                thumbnail_image_bytes: bytes = thumbnail_response.read(
                    self.maximum_thumbnail_byte_count + 1
                )
        except OSError as thumbnail_network_error:
            # PROVENANCE: urllib.error.URLError/HTTPError and socket timeouts all subclass OSError.
            raise ThumbnailImageFetchFailedError(str(thumbnail_network_error)) from (
                thumbnail_network_error
            )
        if len(thumbnail_image_bytes) > self.maximum_thumbnail_byte_count:
            raise ThumbnailImageFetchFailedError("thumbnail exceeds the byte limit")
        return thumbnail_image_bytes
