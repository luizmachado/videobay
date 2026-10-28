from dataclasses import dataclass

from videobay_gui.core.inspected_media_summary import (
    InspectedPlaylistEntry,
    format_media_duration_for_display,
)

PLAYLIST_ITEMS_PER_PAGE = 50


@dataclass(frozen=True)
class PlaylistItemRowViewModel:
    playlist_item_index: int
    item_label: str
    is_item_selectable: bool
    is_item_checked: bool


@dataclass(frozen=True)
class PlaylistItemPageViewModel:
    item_rows: tuple[PlaylistItemRowViewModel, ...]
    current_page_number: int
    page_label: str
    can_go_to_previous_page: bool
    can_go_to_next_page: bool
    selected_item_count_label: str


def build_playlist_item_page_view_model(
    inspected_playlist_entries: tuple[InspectedPlaylistEntry, ...],
    selected_playlist_item_indices: tuple[int, ...],
    page_number: int,
) -> PlaylistItemPageViewModel:
    # WHY: EC-12. Paging keeps a 1000-item playlist from creating 1000 Tk widgets at once.
    page_count = max(1, -(-len(inspected_playlist_entries) // PLAYLIST_ITEMS_PER_PAGE))
    current_page_number = min(max(page_number, 1), page_count)
    first_entry_offset = (current_page_number - 1) * PLAYLIST_ITEMS_PER_PAGE
    # WHY: named end offset, because ruff format spaces a complex slice (`a : a + n`) and the
    # upstream autopep8 check (E203) rejects that space.
    page_end_entry_offset = first_entry_offset + PLAYLIST_ITEMS_PER_PAGE
    entries_on_page = inspected_playlist_entries[first_entry_offset:page_end_entry_offset]
    selected_index_set = set(selected_playlist_item_indices)
    return PlaylistItemPageViewModel(
        item_rows=tuple(
            build_playlist_item_row_view_model(playlist_entry, selected_index_set)
            for playlist_entry in entries_on_page
        ),
        current_page_number=current_page_number,
        page_label=f"Página {current_page_number} de {page_count}",
        can_go_to_previous_page=current_page_number > 1,
        can_go_to_next_page=current_page_number < page_count,
        selected_item_count_label=(
            f"{len(selected_index_set)} de {len(inspected_playlist_entries)} marcados"
        ),
    )


def build_playlist_item_row_view_model(
    playlist_entry: InspectedPlaylistEntry, selected_index_set: set[int]
) -> PlaylistItemRowViewModel:
    item_label = f"{playlist_entry.playlist_item_index}. {playlist_entry.playlist_entry_title}"
    entry_duration_seconds = playlist_entry.playlist_entry_duration_seconds
    if entry_duration_seconds is not None:
        item_label += f" ({format_media_duration_for_display(entry_duration_seconds)})"
    return PlaylistItemRowViewModel(
        playlist_item_index=playlist_entry.playlist_item_index,
        item_label=item_label,
        is_item_selectable=playlist_entry.is_playlist_entry_available,
        is_item_checked=playlist_entry.is_playlist_entry_available
        and playlist_entry.playlist_item_index in selected_index_set,
    )
