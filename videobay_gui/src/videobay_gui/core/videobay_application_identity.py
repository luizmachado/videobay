VIDEOBAY_APPLICATION_DISPLAY_NAME = "VideoBay"


def build_videobay_main_window_title(videobay_application_version: str) -> str:
    stripped_videobay_application_version = videobay_application_version.strip()
    if not stripped_videobay_application_version:
        return VIDEOBAY_APPLICATION_DISPLAY_NAME
    return f"{VIDEOBAY_APPLICATION_DISPLAY_NAME} {stripped_videobay_application_version}"
