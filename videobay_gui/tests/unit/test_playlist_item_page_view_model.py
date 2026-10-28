import pytest

from videobay_gui.core.inspected_media_summary import InspectedPlaylistEntry
from videobay_gui.core.playlist_item_page_view_model import (
    PLAYLIST_ITEMS_PER_PAGE,
    build_playlist_item_page_view_model,
)

PRIVATE_ITEM_INDEX = 2
HUNDRED_AND_TWENTY_ENTRIES = tuple(
    InspectedPlaylistEntry(item_index, f"Aula {item_index}", 90, item_index != PRIVATE_ITEM_INDEX)
    for item_index in range(1, 121)
)


def test_first_page_shows_fifty_items_with_labels_and_navigation():
    page_view_model = build_playlist_item_page_view_model(
        HUNDRED_AND_TWENTY_ENTRIES, (1, 3), page_number=1
    )

    assert len(page_view_model.item_rows) == PLAYLIST_ITEMS_PER_PAGE
    assert page_view_model.item_rows[0].item_label == "1. Aula 1 (1:30)"
    assert page_view_model.page_label == "Página 1 de 3"
    assert (page_view_model.can_go_to_previous_page, page_view_model.can_go_to_next_page) == (
        False,
        True,
    )
    assert page_view_model.selected_item_count_label == "2 de 120 marcados"


def test_ec11_unavailable_items_are_unchecked_and_not_selectable():
    second_row = build_playlist_item_page_view_model(
        HUNDRED_AND_TWENTY_ENTRIES, (1, 2, 3), page_number=1
    ).item_rows[1]

    assert second_row.is_item_selectable is False
    assert second_row.is_item_checked is False


def test_checked_state_follows_the_selected_indices_on_other_pages():
    last_page = build_playlist_item_page_view_model(
        HUNDRED_AND_TWENTY_ENTRIES, (101, 120), page_number=3
    )

    assert [row.playlist_item_index for row in last_page.item_rows][0] == 101  # noqa: PLR2004
    assert [row.is_item_checked for row in last_page.item_rows if row.is_item_checked] == [
        True,
        True,
    ]
    assert (last_page.can_go_to_previous_page, last_page.can_go_to_next_page) == (True, False)


@pytest.mark.parametrize(
    ("requested_page", "expected_label"), [(0, "Página 1 de 3"), (9, "Página 3 de 3")]
)
def test_out_of_range_pages_are_clamped(requested_page: int, expected_label: str):
    assert (
        build_playlist_item_page_view_model(
            HUNDRED_AND_TWENTY_ENTRIES, (), page_number=requested_page
        ).page_label
        == expected_label
    )


def test_item_without_duration_has_no_time_suffix():
    page_view_model = build_playlist_item_page_view_model(
        (InspectedPlaylistEntry(1, "Ao vivo", None, True),), (1,), page_number=1
    )

    assert page_view_model.item_rows[0].item_label == "1. Ao vivo"
    assert page_view_model.current_page_number == 1
