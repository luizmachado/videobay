from dataclasses import replace

from tests.unit.media_inspection_presenter_harness import (
    SAMPLE_VIDEO_URL,
    MediaInspectionPresenterTestHarness,
    build_sample_inspected_media_summary,
    presenter_harness,
)
from videobay_gui.core.inspected_media_summary import InspectedPlaylistEntry
from videobay_gui.core.playlist_item_page_view_model import PlaylistItemPageViewModel

__all__ = ["presenter_harness"]

SEVENTY_ENTRIES_WITH_PRIVATE_SECOND = tuple(
    InspectedPlaylistEntry(item_index, f"Aula {item_index}", 60, item_index != 2)  # noqa: PLR2004
    for item_index in range(1, 71)
)


def inspect_seventy_item_playlist(presenter_harness: MediaInspectionPresenterTestHarness) -> None:
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        replace(
            build_sample_inspected_media_summary(),
            inspected_playlist_entries=SEVENTY_ENTRIES_WITH_PRIVATE_SECOND,
        )
    )
    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)


def last_shown_page(
    presenter_harness: MediaInspectionPresenterTestHarness,
) -> PlaylistItemPageViewModel:
    return presenter_harness.media_inspection_view_fake.last_recorded_argument_of(
        "show_playlist_item_page"
    )


def selected_indices(presenter_harness: MediaInspectionPresenterTestHarness) -> tuple[int, ...]:
    current_selection = presenter_harness.media_inspection_presenter.current_download_selection()
    assert current_selection is not None
    return current_selection.selected_playlist_item_indices_for_download


def test_ec12_inspected_playlist_shows_first_page_with_available_items_checked(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_seventy_item_playlist(presenter_harness)

    first_page = last_shown_page(presenter_harness)
    assert first_page.page_label == "Página 1 de 2"
    assert first_page.selected_item_count_label == "69 de 70 marcados"


def test_single_video_hides_the_item_list(presenter_harness: MediaInspectionPresenterTestHarness):
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        build_sample_inspected_media_summary()
    )

    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)

    assert last_shown_page(presenter_harness) is None


def test_ec12_requested_page_is_shown_and_keeps_selection(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_seventy_item_playlist(presenter_harness)

    presenter_harness.media_inspection_presenter.handle_playlist_page_requested(2)

    second_page = last_shown_page(presenter_harness)
    assert second_page.page_label == "Página 2 de 2"
    assert second_page.item_rows[0].playlist_item_index == 51  # noqa: PLR2004
    assert second_page.item_rows[0].is_item_checked


def test_toggling_an_item_updates_selection_and_redraws_the_same_page(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_seventy_item_playlist(presenter_harness)
    presenter_harness.media_inspection_presenter.handle_playlist_page_requested(2)

    presenter_harness.media_inspection_presenter.handle_playlist_item_checkbox_toggled(51, False)

    assert 51 not in selected_indices(presenter_harness)  # noqa: PLR2004
    assert last_shown_page(presenter_harness).page_label == "Página 2 de 2"
    assert last_shown_page(presenter_harness).selected_item_count_label == "68 de 70 marcados"
    presenter_harness.media_inspection_presenter.handle_playlist_item_checkbox_toggled(51, True)
    assert 51 in selected_indices(presenter_harness)  # noqa: PLR2004


def test_check_all_skips_unavailable_items_and_uncheck_all_empties_selection(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_seventy_item_playlist(presenter_harness)

    presenter_harness.media_inspection_presenter.handle_all_playlist_items_toggled(False)
    assert selected_indices(presenter_harness) == ()
    presenter_harness.media_inspection_presenter.handle_all_playlist_items_toggled(True)

    assert 2 not in selected_indices(presenter_harness)  # noqa: PLR2004
    assert len(selected_indices(presenter_harness)) == 69  # noqa: PLR2004


def test_paging_without_an_inspected_playlist_does_nothing(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    presenter_harness.media_inspection_presenter.handle_playlist_page_requested(2)
    presenter_harness.media_inspection_presenter.handle_playlist_item_checkbox_toggled(1, True)
    presenter_harness.media_inspection_presenter.handle_all_playlist_items_toggled(True)

    assert "show_playlist_item_page" not in (
        presenter_harness.media_inspection_view_fake.recorded_view_call_names()
    )
