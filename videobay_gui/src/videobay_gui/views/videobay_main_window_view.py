# pyright: basic
# WHY: customtkinter has no type information, so strict mode would flag
# every widget call as Unknown.
# Views stay thin (ADR-0003); all logic lives in the strictly typed core.
from collections.abc import Callable

import customtkinter

from videobay_gui.views.media_inspection_panel_view import MediaInspectionPanelView
from videobay_gui.views.single_media_download_panel_view import SingleMediaDownloadPanelView

VIDEOBAY_MAIN_WINDOW_INITIAL_GEOMETRY = "820x620"
VIDEOBAY_MAIN_WINDOW_MINIMUM_SIZE = (680, 560)


class VideobayMainWindowView(customtkinter.CTk):
    def __init__(self, videobay_main_window_title: str) -> None:
        super().__init__()
        customtkinter.set_appearance_mode("system")
        self.title(videobay_main_window_title)
        self.geometry(VIDEOBAY_MAIN_WINDOW_INITIAL_GEOMETRY)
        self.minsize(*VIDEOBAY_MAIN_WINDOW_MINIMUM_SIZE)
        self.media_inspection_panel_view = MediaInspectionPanelView(self)
        self.media_inspection_panel_view.pack(fill="x")
        self.single_media_download_panel_view = SingleMediaDownloadPanelView(self)
        self.single_media_download_panel_view.pack(fill="x", padx=16, pady=(0, 16))

    def schedule_recurring_ui_callback(
        self, callback_interval_milliseconds: int, recurring_ui_callback: Callable[[], object]
    ) -> None:
        # PROVENANCE: ADR-0004. Worker results only reach widgets through this Tk-thread loop.
        def run_and_reschedule_recurring_ui_callback() -> None:
            recurring_ui_callback()
            self.after(callback_interval_milliseconds, run_and_reschedule_recurring_ui_callback)

        self.after(callback_interval_milliseconds, run_and_reschedule_recurring_ui_callback)

    def bind_main_window_close_callback(self, on_main_window_closing: Callable[[], None]) -> None:
        def close_main_window() -> None:
            on_main_window_closing()
            self.destroy()

        self.protocol("WM_DELETE_WINDOW", close_main_window)

    def run_videobay_main_event_loop(self) -> None:
        self.mainloop()
