import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from videobay_gui.adapters.urllib_thumbnail_image_fetcher_adapter import (
    UrllibThumbnailImageFetcherAdapter,
)
from videobay_gui.core.thumbnail_image_fetch_failure import ThumbnailImageFetchFailedError

LOCAL_THUMBNAIL_BYTES = b"\x89PNG\r\n\x1a\nlocal-thumbnail"
OVERSIZED_THUMBNAIL_BYTE_COUNT = 2048


class LocalThumbnailRequestHandlerForTests(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/thumb.png":
            self.respond_with_thumbnail_bytes(LOCAL_THUMBNAIL_BYTES)
            return
        if self.path == "/huge.png":
            self.respond_with_thumbnail_bytes(b"x" * OVERSIZED_THUMBNAIL_BYTE_COUNT)
            return
        self.send_error(404)

    def respond_with_thumbnail_bytes(self, thumbnail_bytes: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Length", str(len(thumbnail_bytes)))
        self.end_headers()
        self.wfile.write(thumbnail_bytes)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return None


@pytest.fixture
def local_thumbnail_server_base_url() -> Iterator[str]:
    local_thumbnail_server = ThreadingHTTPServer(
        ("127.0.0.1", 0), LocalThumbnailRequestHandlerForTests
    )
    server_thread = threading.Thread(target=local_thumbnail_server.serve_forever, daemon=True)
    server_thread.start()
    yield f"http://127.0.0.1:{local_thumbnail_server.server_address[1]}"
    local_thumbnail_server.shutdown()
    local_thumbnail_server.server_close()


def test_downloads_thumbnail_bytes_over_http(local_thumbnail_server_base_url: str):
    thumbnail_fetcher = UrllibThumbnailImageFetcherAdapter()

    assert (
        thumbnail_fetcher.fetch_thumbnail_image_bytes(
            f"{local_thumbnail_server_base_url}/thumb.png"
        )
        == LOCAL_THUMBNAIL_BYTES
    )


def test_ec14_http_error_becomes_thumbnail_fetch_failure(local_thumbnail_server_base_url: str):
    with pytest.raises(ThumbnailImageFetchFailedError):
        UrllibThumbnailImageFetcherAdapter().fetch_thumbnail_image_bytes(
            f"{local_thumbnail_server_base_url}/missing.png"
        )


def test_ec14_unreachable_host_becomes_thumbnail_fetch_failure():
    with pytest.raises(ThumbnailImageFetchFailedError):
        UrllibThumbnailImageFetcherAdapter(
            thumbnail_fetch_timeout_seconds=1
        ).fetch_thumbnail_image_bytes("http://127.0.0.1:9/never-listening.png")


def test_rejects_thumbnails_larger_than_the_byte_limit(local_thumbnail_server_base_url: str):
    size_limited_fetcher = UrllibThumbnailImageFetcherAdapter(
        maximum_thumbnail_byte_count=OVERSIZED_THUMBNAIL_BYTE_COUNT - 1
    )

    with pytest.raises(ThumbnailImageFetchFailedError, match="limit"):
        size_limited_fetcher.fetch_thumbnail_image_bytes(
            f"{local_thumbnail_server_base_url}/huge.png"
        )


@pytest.mark.parametrize(
    "non_web_thumbnail_url", ["file:///etc/passwd", "ftp://x/y.jpg", "data:,x"]
)
def test_refuses_non_http_thumbnail_urls(non_web_thumbnail_url: str):
    with pytest.raises(ThumbnailImageFetchFailedError, match="scheme"):
        UrllibThumbnailImageFetcherAdapter().fetch_thumbnail_image_bytes(non_web_thumbnail_url)
