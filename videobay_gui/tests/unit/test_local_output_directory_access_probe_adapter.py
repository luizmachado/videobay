import os
from pathlib import Path

import pytest

from videobay_gui.adapters.local_output_directory_access_probe_adapter import (
    LocalOutputDirectoryAccessProbeAdapter,
    resolve_default_videobay_output_directory,
)
from videobay_gui.core.videobay_user_settings import OutputDirectoryProblem


def test_writable_existing_directory_has_no_problem(tmp_path: Path):
    assert (
        LocalOutputDirectoryAccessProbeAdapter().find_output_directory_problem(str(tmp_path))
        is None
    )


def test_ec06_missing_directory_is_reported(tmp_path: Path):
    assert (
        LocalOutputDirectoryAccessProbeAdapter().find_output_directory_problem(
            str(tmp_path / "nao-existe")
        )
        == OutputDirectoryProblem.OUTPUT_DIRECTORY_MISSING
    )


def test_ec06_regular_file_is_not_a_directory(tmp_path: Path):
    regular_file = tmp_path / "video.mp4"
    regular_file.write_bytes(b"")

    assert (
        LocalOutputDirectoryAccessProbeAdapter().find_output_directory_problem(str(regular_file))
        == OutputDirectoryProblem.OUTPUT_PATH_IS_NOT_A_DIRECTORY
    )


@pytest.mark.skipif(os.geteuid() == 0, reason="root can write to read-only directories")
def test_ec06_read_only_directory_is_not_writable(tmp_path: Path):
    read_only_directory = tmp_path / "somente-leitura"
    read_only_directory.mkdir(mode=0o555)

    assert (
        LocalOutputDirectoryAccessProbeAdapter().find_output_directory_problem(
            str(read_only_directory)
        )
        == OutputDirectoryProblem.OUTPUT_DIRECTORY_NOT_WRITABLE
    )


def test_default_output_directory_reads_xdg_download_dir(tmp_path: Path):
    (tmp_path / ".config").mkdir()
    (tmp_path / "Transferências").mkdir()
    (tmp_path / ".config" / "user-dirs.dirs").write_text(
        '# comentario\nXDG_DOWNLOAD_DIR="$HOME/Transferências"\n', encoding="utf-8"
    )

    assert resolve_default_videobay_output_directory(str(tmp_path)) == str(
        tmp_path / "Transferências"
    )


def test_default_output_directory_falls_back_to_downloads_then_home(tmp_path: Path):
    assert resolve_default_videobay_output_directory(str(tmp_path)) == str(tmp_path)
    (tmp_path / "Downloads").mkdir()
    assert resolve_default_videobay_output_directory(str(tmp_path)) == str(tmp_path / "Downloads")
