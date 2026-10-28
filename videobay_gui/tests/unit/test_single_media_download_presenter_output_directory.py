import pytest

from tests.unit.single_media_download_presenter_harness import (
    DEFAULT_DOWNLOAD_DIRECTORY,
    SingleMediaDownloadPresenterTestHarness,
    download_harness,
)
from videobay_gui.core.videobay_user_settings import OutputDirectoryProblem

__all__ = ["download_harness"]


def test_initial_state_shows_saved_output_directory(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_presenter.present_initial_download_state()

    assert download_harness.download_view_fake.recorded_arguments_of("show_output_directory") == [
        DEFAULT_DOWNLOAD_DIRECTORY
    ]


def test_choosing_valid_directory_saves_settings_and_shows_it(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_presenter.handle_output_directory_chosen("/media/hd/videos")

    stored_settings = download_harness.settings_store_fake.stored_videobay_user_settings
    assert stored_settings.preferred_output_directory == "/media/hd/videos"
    assert download_harness.download_view_fake.recorded_arguments_of("show_output_directory") == [
        "/media/hd/videos"
    ]


@pytest.mark.parametrize("cancelled_dialog_path", ["", "   "])
def test_cancelled_folder_dialog_changes_nothing(
    download_harness: SingleMediaDownloadPresenterTestHarness, cancelled_dialog_path: str
):
    download_harness.download_presenter.handle_output_directory_chosen(cancelled_dialog_path)

    assert download_harness.settings_store_fake.save_call_count == 0
    assert download_harness.download_view_fake.recorded_view_calls == []


def test_ec06_choosing_unwritable_directory_is_rejected_with_message(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.output_directory_probe_fake.output_directory_problems_by_path["/root"] = (
        OutputDirectoryProblem.OUTPUT_DIRECTORY_NOT_WRITABLE
    )

    download_harness.download_presenter.handle_output_directory_chosen("/root")

    assert download_harness.settings_store_fake.save_call_count == 0
    assert (
        "/root"
        in download_harness.download_view_fake.recorded_arguments_of("show_download_notice")[-1]
    )


def test_ec06_download_into_folder_that_disappeared_is_blocked_before_queueing(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.output_directory_probe_fake.output_directory_problems_by_path[
        DEFAULT_DOWNLOAD_DIRECTORY
    ] = OutputDirectoryProblem.OUTPUT_DIRECTORY_MISSING

    download_harness.request_download_and_drain()

    assert download_harness.download_executor_fake.executed_downloads == []
    assert (
        "não existe"
        in download_harness.download_view_fake.recorded_arguments_of("show_download_notice")[-1]
    )
