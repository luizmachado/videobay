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


@pytest.mark.parametrize("should_main_window_close", [False, True])
def test_ec16_window_close_honours_the_presenter_answer(should_main_window_close: bool):
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

    videobay_main_window_view = VideobayMainWindowView("VideoBay close")
    closing_callback_calls: list[str] = []
    videobay_main_window_view.bind_main_window_close_callback(
        lambda: should_main_window_close, lambda: closing_callback_calls.append("closing")
    )
    videobay_main_window_view.update()

    # PROVENANCE: Tk's protocol() returns the registered Tcl command name, not a Python callable.
    videobay_main_window_view.tk.call(videobay_main_window_view.protocol("WM_DELETE_WINDOW"))

    assert closing_callback_calls == (["closing"] if should_main_window_close else [])
    if not should_main_window_close:
        assert videobay_main_window_view.winfo_exists()
        videobay_main_window_view.destroy()
