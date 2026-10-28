from videobay_gui.core.videobay_application_identity import (
    build_videobay_main_window_title,
)


def test_main_window_title_includes_application_name_and_version():
    assert build_videobay_main_window_title("0.1.0") == "VideoBay 0.1.0"


def test_main_window_title_omits_version_when_version_is_blank():
    assert build_videobay_main_window_title("  ") == "VideoBay"
