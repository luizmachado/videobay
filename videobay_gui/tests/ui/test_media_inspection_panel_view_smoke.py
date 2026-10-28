# pyright: basic
# WHY: drives real CustomTkinter widgets (untyped) wired to the real presenter and test fakes.
import io
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from tests.fakes.in_memory_media_metadata_extractor_fake import InMemoryMediaMetadataExtractorFake
from tests.fakes.manually_drained_background_worker_pool_fake import (
    ManuallyDrainedBackgroundWorkerPoolFake,
)
from tests.fakes.static_thumbnail_image_fetcher_fake import StaticThumbnailImageFetcherFake
from videobay_gui.core.inspected_media_summary import InspectedMediaSummary
from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailedError,
    MediaInspectionFailureKind,
)
from videobay_gui.core.media_inspection_presenter import MediaInspectionPresenter

if TYPE_CHECKING:
    from videobay_gui.views.media_inspection_panel_view import MediaInspectionPanelView
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

pytestmark = pytest.mark.ui

SMOKE_VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
SMOKE_THUMBNAIL_URL = "https://i.ytimg.com/vi/jNQXAC9IVRw/hqdefault.jpg"


def encode_solid_color_jpeg_thumbnail() -> bytes:
    jpeg_buffer = io.BytesIO()
    Image.new("RGB", (480, 360), (200, 40, 40)).save(jpeg_buffer, format="JPEG")
    return jpeg_buffer.getvalue()


@dataclass
class MediaInspectionPanelSmokeRig:
    main_window_view: "VideobayMainWindowView"
    panel_view: "MediaInspectionPanelView"
    extractor_fake: InMemoryMediaMetadataExtractorFake
    worker_pool_fake: ManuallyDrainedBackgroundWorkerPoolFake
    thumbnail_fetcher_fake: StaticThumbnailImageFetcherFake

    def type_url_click_search_and_finish_background(self, typed_media_url: str) -> None:
        self.panel_view.media_url_text_variable.set(typed_media_url)
        self.panel_view.inspect_media_url_button.invoke()
        self.worker_pool_fake.drain_pending_background_tasks()
        self.worker_pool_fake.drain_pending_background_tasks()
        self.main_window_view.update()


@pytest.fixture
def smoke_rig() -> Iterator[MediaInspectionPanelSmokeRig]:
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

    main_window_view = VideobayMainWindowView("VideoBay smoke")
    panel_view = main_window_view.media_inspection_panel_view
    smoke_rig = MediaInspectionPanelSmokeRig(
        main_window_view,
        panel_view,
        InMemoryMediaMetadataExtractorFake(),
        ManuallyDrainedBackgroundWorkerPoolFake(),
        StaticThumbnailImageFetcherFake(),
    )
    media_inspection_presenter = MediaInspectionPresenter(
        panel_view,
        smoke_rig.extractor_fake,
        smoke_rig.worker_pool_fake,
        smoke_rig.thumbnail_fetcher_fake,
    )
    panel_view.bind_media_inspection_presenter_callbacks(
        media_inspection_presenter.handle_media_url_text_changed,
        media_inspection_presenter.handle_inspect_media_url_requested,
    )
    main_window_view.update()
    yield smoke_rig
    main_window_view.destroy()


def test_ec01_typing_invalid_url_shows_message_and_keeps_search_disabled(
    smoke_rig: MediaInspectionPanelSmokeRig,
):
    smoke_rig.panel_view.media_url_text_variable.set("youtube.com/watch")
    smoke_rig.main_window_view.update()

    assert "http" in smoke_rig.panel_view.media_url_validation_label.cget("text")
    assert smoke_rig.panel_view.inspect_media_url_button.cget("state") == "disabled"


def test_inspected_video_fills_card_quality_menu_and_thumbnail(
    smoke_rig: MediaInspectionPanelSmokeRig,
):
    smoke_rig.extractor_fake.script_media_summary(
        InspectedMediaSummary(
            media_url=SMOKE_VIDEO_URL,
            media_title="Me at the zoo",
            media_uploader_name="jawed",
            media_duration_seconds=19,
            media_thumbnail_url=SMOKE_THUMBNAIL_URL,
            is_live_broadcast=False,
            available_video_heights=(240, 144),
        )
    )
    smoke_rig.thumbnail_fetcher_fake.script_thumbnail_image_bytes(
        SMOKE_THUMBNAIL_URL, encode_solid_color_jpeg_thumbnail()
    )

    smoke_rig.type_url_click_search_and_finish_background(SMOKE_VIDEO_URL)

    panel_view = smoke_rig.panel_view
    assert panel_view.media_title_label.cget("text") == "Me at the zoo"
    assert panel_view.media_details_label.cget("text") == "jawed  ·  0:19"
    assert panel_view.selected_media_quality_choice_label() == "Melhor (240p)"
    assert panel_view.media_quality_option_menu.cget("values") == [
        "Melhor (240p)",
        "Até 144p",
        "Só áudio",
    ]
    assert panel_view.media_thumbnail_ctk_image is not None
    assert panel_view.media_thumbnail_label.cget("text") == ""


def test_ec14_undecodable_thumbnail_bytes_fall_back_to_placeholder(
    smoke_rig: MediaInspectionPanelSmokeRig,
):
    smoke_rig.extractor_fake.script_media_summary(
        InspectedMediaSummary(
            media_url=SMOKE_VIDEO_URL,
            media_title="x",
            media_uploader_name=None,
            media_duration_seconds=None,
            media_thumbnail_url=SMOKE_THUMBNAIL_URL,
            is_live_broadcast=False,
        )
    )
    smoke_rig.thumbnail_fetcher_fake.script_thumbnail_image_bytes(
        SMOKE_THUMBNAIL_URL, b"<html>not an image</html>"
    )

    smoke_rig.type_url_click_search_and_finish_background(SMOKE_VIDEO_URL)

    assert smoke_rig.panel_view.media_thumbnail_ctk_image is None
    assert smoke_rig.panel_view.media_thumbnail_label.cget("text") == "Sem miniatura"


def test_ec03_retryable_failure_shows_message_and_retry_button(
    smoke_rig: MediaInspectionPanelSmokeRig,
):
    smoke_rig.extractor_fake.script_extraction_error(
        SMOKE_VIDEO_URL,
        MediaInspectionFailedError(MediaInspectionFailureKind.NETWORK_UNREACHABLE, "timeout"),
    )

    smoke_rig.type_url_click_search_and_finish_background(SMOKE_VIDEO_URL)

    assert "Sem conexão" in smoke_rig.panel_view.media_title_label.cget("text")
    assert smoke_rig.panel_view.retry_media_inspection_button.winfo_ismapped()

    smoke_rig.panel_view.retry_media_inspection_button.invoke()
    assert smoke_rig.extractor_fake.extracted_media_urls == [SMOKE_VIDEO_URL]
    smoke_rig.worker_pool_fake.drain_pending_background_tasks()
    assert smoke_rig.extractor_fake.extracted_media_urls == [SMOKE_VIDEO_URL, SMOKE_VIDEO_URL]
