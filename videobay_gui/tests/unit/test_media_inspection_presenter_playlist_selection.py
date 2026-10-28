from dataclasses import replace

from tests.unit.media_inspection_presenter_harness import (
    SAMPLE_VIDEO_URL,
    MediaInspectionPresenterTestHarness,
    build_sample_inspected_media_summary,
    presenter_harness,
)
from videobay_gui.core.inspected_media_summary import InspectedPlaylistEntry

__all__ = ["presenter_harness"]

SAMPLE_PLAYLIST_ENTRIES = (
    InspectedPlaylistEntry(1, "Aula 1", 60, True),
    InspectedPlaylistEntry(2, "[Private video]", None, False),
    InspectedPlaylistEntry(3, "Aula 3", 60, True),
)


def inspect_sample_playlist(presenter_harness: MediaInspectionPresenterTestHarness) -> None:
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        replace(
            build_sample_inspected_media_summary(),
            inspected_playlist_entries=SAMPLE_PLAYLIST_ENTRIES,
        )
    )
    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)


def test_ec11_playlist_selection_defaults_to_every_available_item(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_sample_playlist(presenter_harness)

    current_selection = presenter_harness.media_inspection_presenter.current_download_selection()

    assert current_selection is not None
    assert current_selection.is_playlist_selection
    assert current_selection.selected_playlist_item_indices_for_download == (1, 3)


def test_changed_item_selection_is_used_for_download(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_sample_playlist(presenter_harness)

    presenter_harness.media_inspection_presenter.handle_playlist_item_selection_changed((3,))

    current_selection = presenter_harness.media_inspection_presenter.current_download_selection()
    assert current_selection is not None
    assert current_selection.selected_playlist_item_indices_for_download == (3,)


def test_new_inspection_resets_item_selection(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_sample_playlist(presenter_harness)
    presenter_harness.media_inspection_presenter.handle_playlist_item_selection_changed((3,))

    inspect_sample_playlist(presenter_harness)

    current_selection = presenter_harness.media_inspection_presenter.current_download_selection()
    assert current_selection is not None
    assert current_selection.selected_playlist_item_indices_for_download == (1, 3)


def test_single_video_selection_is_not_a_playlist(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        build_sample_inspected_media_summary()
    )
    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)

    current_selection = presenter_harness.media_inspection_presenter.current_download_selection()
    assert current_selection is not None
    assert not current_selection.is_playlist_selection
    assert current_selection.selected_playlist_item_indices_for_download == ()
