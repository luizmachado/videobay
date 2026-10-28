import os
import subprocess
from pathlib import Path

VIDEOBAY_GUI_PROJECT_ROOT = Path(__file__).resolve().parents[2]
VIDEOBAY_INSTALL_SCRIPT = (
    VIDEOBAY_GUI_PROJECT_ROOT / "deploy" / "install_videobay_gui_binary_by_git_sha.sh"
)
VIDEOBAY_ROLLBACK_SCRIPT = (
    VIDEOBAY_GUI_PROJECT_ROOT / "deploy" / "rollback_videobay_gui_to_previous_git_sha.sh"
)


def build_isolated_videobay_home_environment(fake_home_directory: Path) -> dict[str, str]:
    return {
        **os.environ,
        "HOME": str(fake_home_directory),
        "XDG_DATA_HOME": str(fake_home_directory / "data"),
        "XDG_STATE_HOME": str(fake_home_directory / "state"),
    }


def write_fake_videobay_binary(fake_dist_directory: Path, binary_marker_text: str) -> Path:
    fake_videobay_binary = fake_dist_directory / binary_marker_text / "videobay-gui"
    fake_videobay_binary.parent.mkdir(parents=True)
    fake_videobay_binary.write_text(f"#!/bin/sh\necho {binary_marker_text}\n")
    fake_videobay_binary.chmod(0o755)
    return fake_videobay_binary


def run_videobay_deploy_script(script_arguments: list[str], environment: dict[str, str]):
    return subprocess.run(script_arguments, env=environment, capture_output=True, text=True)


def read_installed_videobay_symlink_target(fake_home_directory: Path) -> str:
    return os.readlink(fake_home_directory / ".local" / "bin" / "videobay-gui")


def test_install_points_symlink_at_versioned_binary(tmp_path: Path):
    environment = build_isolated_videobay_home_environment(tmp_path)
    first_binary = write_fake_videobay_binary(tmp_path / "dist", "sha111")

    install_result = run_videobay_deploy_script(
        [str(VIDEOBAY_INSTALL_SCRIPT), "sha111", str(first_binary)], environment
    )

    assert install_result.returncode == 0, install_result.stderr
    assert read_installed_videobay_symlink_target(tmp_path).endswith("/sha111/videobay-gui")


def test_rollback_restores_previous_sha_and_second_rollback_rolls_forward(tmp_path: Path):
    environment = build_isolated_videobay_home_environment(tmp_path)
    for git_sha in ("sha111", "sha222"):
        fake_binary = write_fake_videobay_binary(tmp_path / "dist", git_sha)
        run_videobay_deploy_script(
            [str(VIDEOBAY_INSTALL_SCRIPT), git_sha, str(fake_binary)], environment
        )

    first_rollback = run_videobay_deploy_script([str(VIDEOBAY_ROLLBACK_SCRIPT)], environment)
    assert first_rollback.returncode == 0, first_rollback.stderr
    assert read_installed_videobay_symlink_target(tmp_path).endswith("/sha111/videobay-gui")

    run_videobay_deploy_script([str(VIDEOBAY_ROLLBACK_SCRIPT)], environment)
    assert read_installed_videobay_symlink_target(tmp_path).endswith("/sha222/videobay-gui")


def test_rollback_fails_cleanly_when_nothing_was_installed_before(tmp_path: Path):
    environment = build_isolated_videobay_home_environment(tmp_path)

    rollback_result = run_videobay_deploy_script([str(VIDEOBAY_ROLLBACK_SCRIPT)], environment)

    assert rollback_result.returncode != 0
    assert "no previous" in rollback_result.stderr.lower()


def test_install_rejects_missing_binary(tmp_path: Path):
    environment = build_isolated_videobay_home_environment(tmp_path)

    install_result = run_videobay_deploy_script(
        [str(VIDEOBAY_INSTALL_SCRIPT), "sha999", str(tmp_path / "missing")], environment
    )

    assert install_result.returncode != 0
    assert "not found" in install_result.stderr.lower()
