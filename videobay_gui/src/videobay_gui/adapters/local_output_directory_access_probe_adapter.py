import os
import re

from videobay_gui.core.videobay_user_settings import OutputDirectoryProblem

# PROVENANCE: xdg-user-dirs format, e.g. XDG_DOWNLOAD_DIR="$HOME/Transferências" in
# ~/.config/user-dirs.dirs; localized desktops rename the folder, so the name cannot be hardcoded.
XDG_DOWNLOAD_DIRECTORY_LINE_PATTERN = re.compile(r'^XDG_DOWNLOAD_DIR="(?P<download_path>[^"]+)"')


class LocalOutputDirectoryAccessProbeAdapter:
    def find_output_directory_problem(self, output_directory: str) -> OutputDirectoryProblem | None:
        if not os.path.exists(output_directory):
            return OutputDirectoryProblem.OUTPUT_DIRECTORY_MISSING
        if not os.path.isdir(output_directory):
            return OutputDirectoryProblem.OUTPUT_PATH_IS_NOT_A_DIRECTORY
        if not os.access(output_directory, os.W_OK | os.X_OK):
            return OutputDirectoryProblem.OUTPUT_DIRECTORY_NOT_WRITABLE
        return None


def resolve_default_videobay_output_directory(user_home_directory: str) -> str:
    xdg_download_directory = read_xdg_download_directory(user_home_directory)
    if xdg_download_directory is not None and os.path.isdir(xdg_download_directory):
        return xdg_download_directory
    english_downloads_directory = os.path.join(user_home_directory, "Downloads")
    if os.path.isdir(english_downloads_directory):
        return english_downloads_directory
    return user_home_directory


def read_xdg_download_directory(user_home_directory: str) -> str | None:
    user_dirs_file_path = os.path.join(user_home_directory, ".config", "user-dirs.dirs")
    try:
        with open(user_dirs_file_path, encoding="utf-8") as user_dirs_file:
            user_dirs_lines = user_dirs_file.read().splitlines()
    except OSError:
        return None
    for user_dirs_line in user_dirs_lines:
        download_directory_match = XDG_DOWNLOAD_DIRECTORY_LINE_PATTERN.match(user_dirs_line)
        if download_directory_match:
            return download_directory_match["download_path"].replace("$HOME", user_home_directory)
    return None
