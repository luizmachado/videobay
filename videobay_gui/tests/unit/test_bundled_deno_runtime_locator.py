from pathlib import Path

from videobay_gui.adapters.bundled_deno_runtime_locator import (
    BUNDLED_DENO_EXECUTABLE_NAME,
    locate_deno_executable_for_yt_dlp,
)


def write_fake_executable(executable_path: Path) -> Path:
    executable_path.write_text("#!/bin/sh\n")
    executable_path.chmod(0o755)
    return executable_path


def never_find_on_path(_executable_name: str) -> str | None:
    return None


def test_prefers_deno_bundled_inside_frozen_binary(tmp_path: Path):
    bundled_deno = write_fake_executable(tmp_path / BUNDLED_DENO_EXECUTABLE_NAME)

    assert locate_deno_executable_for_yt_dlp(str(tmp_path), lambda _name: "/usr/bin/deno") == str(
        bundled_deno
    )


def test_falls_back_to_deno_on_path_when_running_from_source():
    assert locate_deno_executable_for_yt_dlp(None, lambda _name: "/usr/bin/deno") == (
        "/usr/bin/deno"
    )


def test_falls_back_to_path_when_bundle_lacks_deno(tmp_path: Path):
    assert locate_deno_executable_for_yt_dlp(str(tmp_path), lambda _name: "/opt/deno") == (
        "/opt/deno"
    )


def test_ignores_bundled_file_that_is_not_executable(tmp_path: Path):
    (tmp_path / BUNDLED_DENO_EXECUTABLE_NAME).write_text("not executable")

    assert locate_deno_executable_for_yt_dlp(str(tmp_path), never_find_on_path) is None


def test_returns_none_when_no_deno_anywhere():
    assert locate_deno_executable_for_yt_dlp(None, never_find_on_path) is None
