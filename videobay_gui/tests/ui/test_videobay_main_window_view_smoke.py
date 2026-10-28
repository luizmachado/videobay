# pyright: basic
# WHY: exercises untyped customtkinter widgets directly (see videobay_main_window_view.py).
import pytest

pytestmark = pytest.mark.ui


def test_main_window_view_renders_with_given_title():
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

    videobay_main_window_view = VideobayMainWindowView("VideoBay 9.9.9")
    try:
        videobay_main_window_view.update()
        assert videobay_main_window_view.title() == "VideoBay 9.9.9"
        assert videobay_main_window_view.media_inspection_panel_view.winfo_ismapped()
    finally:
        videobay_main_window_view.destroy()
