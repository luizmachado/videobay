# pyright: basic
# WHY: drives real CustomTkinter widgets (untyped) wired to the real presenter and test fakes.
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from tests.fakes.in_memory_media_metadata_extractor_fake import InMemoryMediaMetadataExtractorFake
from tests.fakes.manually_drained_background_worker_pool_fake import (
    ManuallyDrainedBackgroundWorkerPoolFake,
)
from tests.fakes.static_thumbnail_image_fetcher_fake import StaticThumbnailImageFetcherFake
from videobay_gui.core.inspected_media_summary import InspectedMediaSummary, InspectedPlaylistEntry
from videobay_gui.core.media_inspection_presenter import MediaInspectionPresenter

if TYPE_CHECKING:
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

pytestmark = pytest.mark.ui

SMOKE_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLsmoke"
SMOKE_SINGLE_VIDEO_URL = "https://youtu.be/single"


@dataclass
class PlaylistPickerSmokeRig:
    main_window_view: "VideobayMainWindowView"
    inspection_presenter: MediaInspectionPresenter
    extractor_fake: InMemoryMediaMetadataExtractorFake
    worker_pool_fake: ManuallyDrainedBackgroundWorkerPoolFake

    def inspect(self, media_url: str) -> None:
        panel_view = self.main_window_view.media_inspection_panel_view
        panel_view.media_url_text_variable.set(media_url)
        panel_view.inspect_media_url_button.invoke()
        self.worker_pool_fake.drain_pending_background_tasks()
        self.main_window_view.update()


@pytest.fixture
def smoke_rig() -> Iterator[PlaylistPickerSmokeRig]:
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

    main_window_view = VideobayMainWindowView("VideoBay playlist smoke")
    panel_view = main_window_view.media_inspection_panel_view
    extractor_fake = InMemoryMediaMetadataExtractorFake()
    worker_pool_fake = ManuallyDrainedBackgroundWorkerPoolFake()
    inspection_presenter = MediaInspectionPresenter(
        panel_view, extractor_fake, worker_pool_fake, StaticThumbnailImageFetcherFake()
    )
    panel_view.bind_media_inspection_presenter_callbacks(
        inspection_presenter.handle_media_url_text_changed,
        inspection_presenter.handle_inspect_media_url_requested,
        inspection_presenter.handle_media_quality_choice_selected,
    )
    panel_view.bind_playlist_and_subtitle_callbacks(
        inspection_presenter.handle_subtitle_language_selection_changed,
        inspection_presenter.handle_playlist_page_requested,
        inspection_presenter.handle_playlist_item_checkbox_toggled,
        inspection_presenter.handle_all_playlist_items_toggled,
    )
    extractor_fake.script_media_summary(
        InspectedMediaSummary(
            media_url=SMOKE_PLAYLIST_URL,
            media_title="Curso",
            media_uploader_name="Canal",
            media_duration_seconds=None,
            media_thumbnail_url=None,
            is_live_broadcast=False,
            inspected_playlist_entries=tuple(
                InspectedPlaylistEntry(item_index, f"Aula {item_index}", 60, item_index != 2)  # noqa: PLR2004
                for item_index in range(1, 71)
            ),
        )
    )
    extractor_fake.script_media_summary(
        InspectedMediaSummary(
            media_url=SMOKE_SINGLE_VIDEO_URL,
            media_title="Vídeo",
            media_uploader_name=None,
            media_duration_seconds=10,
            media_thumbnail_url=None,
            is_live_broadcast=False,
            available_subtitle_languages=("en", "pt-BR"),
        )
    )
    yield PlaylistPickerSmokeRig(
        main_window_view, inspection_presenter, extractor_fake, worker_pool_fake
    )
    main_window_view.destroy()


def test_ec12_playlist_shows_paged_item_list_and_toggles_reach_presenter(
    smoke_rig: PlaylistPickerSmokeRig,
):
    smoke_rig.inspect(SMOKE_PLAYLIST_URL)
    picker_view = smoke_rig.main_window_view.media_inspection_panel_view.playlist_item_picker_view

    assert picker_view.winfo_ismapped()
    assert len(picker_view.item_checkboxes_by_index) == 50  # noqa: PLR2004
    assert picker_view.item_checkboxes_by_index[2].cget("state") == "disabled"

    picker_view.next_page_button.invoke()
    smoke_rig.main_window_view.update()
    assert picker_view.page_label.cget("text") == "Página 2 de 2"

    picker_view.item_checkboxes_by_index[51].toggle()
    current_selection = smoke_rig.inspection_presenter.current_download_selection()
    assert current_selection is not None
    assert 51 not in current_selection.selected_playlist_item_indices_for_download  # noqa: PLR2004
    assert picker_view.selected_item_count_label.cget("text") == "68 de 70 marcados"


def test_single_video_hides_picker_and_subtitle_checkboxes_reach_presenter(
    smoke_rig: PlaylistPickerSmokeRig,
):
    smoke_rig.inspect(SMOKE_PLAYLIST_URL)
    smoke_rig.inspect(SMOKE_SINGLE_VIDEO_URL)
    panel_view = smoke_rig.main_window_view.media_inspection_panel_view

    assert not panel_view.playlist_item_picker_view.winfo_ismapped()
    panel_view.subtitle_checkboxes_by_language["pt-BR"].toggle()

    current_selection = smoke_rig.inspection_presenter.current_download_selection()
    assert current_selection is not None
    assert current_selection.selected_subtitle_languages == ("pt-BR",)
