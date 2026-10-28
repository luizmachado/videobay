import os
from collections.abc import Callable

# PROVENANCE: ADR-0008. `make binary` adds deno with `--add-binary <deno>:.`, so it lands at the
# root of the PyInstaller bundle (sys._MEIPASS) under this name.
BUNDLED_DENO_EXECUTABLE_NAME = "deno"


def locate_deno_executable_for_yt_dlp(
    frozen_bundle_directory: str | None, find_executable_on_path: Callable[[str], str | None]
) -> str | None:
    if frozen_bundle_directory is not None:
        bundled_deno_path = os.path.join(frozen_bundle_directory, BUNDLED_DENO_EXECUTABLE_NAME)
        if os.access(bundled_deno_path, os.X_OK):
            return bundled_deno_path
    return find_executable_on_path(BUNDLED_DENO_EXECUTABLE_NAME)
