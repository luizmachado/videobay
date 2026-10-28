# WHY: the only module allowed to instantiate adapters and views;
# everything else receives them (ADR-0001).
from videobay_gui import __version__
from videobay_gui.core.videobay_application_identity import build_videobay_main_window_title
from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView


def launch_videobay_gui_application() -> None:
    videobay_main_window_view = VideobayMainWindowView(
        build_videobay_main_window_title(__version__)
    )
    videobay_main_window_view.run_videobay_main_event_loop()
