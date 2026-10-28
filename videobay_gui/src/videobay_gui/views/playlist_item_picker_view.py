# pyright: basic
# WHY: customtkinter is untyped; paging, counts and checked state come ready-made from
# PlaylistItemPageViewModel (ADR-0003), so this view only draws and forwards clicks.
from collections.abc import Callable

import customtkinter

from videobay_gui.core.playlist_item_page_view_model import PlaylistItemPageViewModel


class PlaylistItemPickerView(customtkinter.CTkFrame):
    def __init__(self, master: customtkinter.CTkFrame) -> None:
        super().__init__(master, fg_color="transparent")
        self.on_playlist_page_requested: Callable[[int], None] = lambda _page_number: None
        self.on_playlist_item_toggled: Callable[[int, bool], None] = lambda _index, _checked: None
        self.on_all_playlist_items_toggled: Callable[[bool], None] = lambda _check_all: None
        self.current_page_number = 1
        self.item_checkboxes_by_index: dict[int, customtkinter.CTkCheckBox] = {}
        self.build_header_row()
        self.item_list_frame = customtkinter.CTkScrollableFrame(self, height=180)
        self.item_list_frame.pack(fill="both", expand=True, pady=4)
        self.build_page_navigation_row()

    def build_header_row(self) -> None:
        header_row = customtkinter.CTkFrame(self, fg_color="transparent")
        header_row.pack(fill="x")
        self.selected_item_count_label = customtkinter.CTkLabel(header_row, text="", anchor="w")
        self.selected_item_count_label.pack(side="left")
        customtkinter.CTkButton(
            header_row,
            text="Desmarcar todos",
            width=130,
            command=lambda: self.on_all_playlist_items_toggled(False),
        ).pack(side="right")
        customtkinter.CTkButton(
            header_row,
            text="Marcar todos",
            width=120,
            command=lambda: self.on_all_playlist_items_toggled(True),
        ).pack(side="right", padx=(0, 8))

    def build_page_navigation_row(self) -> None:
        navigation_row = customtkinter.CTkFrame(self, fg_color="transparent")
        navigation_row.pack(fill="x")
        self.previous_page_button = customtkinter.CTkButton(
            navigation_row,
            text="◀ Anterior",
            width=110,
            command=lambda: self.on_playlist_page_requested(self.current_page_number - 1),
        )
        self.previous_page_button.pack(side="left")
        self.page_label = customtkinter.CTkLabel(navigation_row, text="")
        self.page_label.pack(side="left", expand=True)
        self.next_page_button = customtkinter.CTkButton(
            navigation_row,
            text="Próxima ▶",
            width=110,
            command=lambda: self.on_playlist_page_requested(self.current_page_number + 1),
        )
        self.next_page_button.pack(side="right")

    def bind_playlist_item_picker_callbacks(
        self,
        on_playlist_page_requested: Callable[[int], None],
        on_playlist_item_toggled: Callable[[int, bool], None],
        on_all_playlist_items_toggled: Callable[[bool], None],
    ) -> None:
        self.on_playlist_page_requested = on_playlist_page_requested
        self.on_playlist_item_toggled = on_playlist_item_toggled
        self.on_all_playlist_items_toggled = on_all_playlist_items_toggled

    def show_playlist_item_page(
        self, playlist_item_page_view_model: PlaylistItemPageViewModel
    ) -> None:
        self.current_page_number = playlist_item_page_view_model.current_page_number
        self.selected_item_count_label.configure(
            text=playlist_item_page_view_model.selected_item_count_label
        )
        self.page_label.configure(text=playlist_item_page_view_model.page_label)
        self.previous_page_button.configure(
            state="normal" if playlist_item_page_view_model.can_go_to_previous_page else "disabled"
        )
        self.next_page_button.configure(
            state="normal" if playlist_item_page_view_model.can_go_to_next_page else "disabled"
        )
        for previous_item_checkbox in self.item_checkboxes_by_index.values():
            previous_item_checkbox.destroy()
        self.item_checkboxes_by_index = {}
        for item_row in playlist_item_page_view_model.item_rows:
            item_checkbox = customtkinter.CTkCheckBox(
                self.item_list_frame,
                text=item_row.item_label,
                state="normal" if item_row.is_item_selectable else "disabled",
                command=lambda item_index=item_row.playlist_item_index: self.forward_item_toggle(
                    item_index
                ),
            )
            if item_row.is_item_checked:
                item_checkbox.select()
            item_checkbox.pack(fill="x", anchor="w", pady=1)
            self.item_checkboxes_by_index[item_row.playlist_item_index] = item_checkbox

    def forward_item_toggle(self, playlist_item_index: int) -> None:
        self.on_playlist_item_toggled(
            playlist_item_index, bool(self.item_checkboxes_by_index[playlist_item_index].get())
        )
