import pytest

from tests.unit.video_download_queue_presenter_harness import (
    DEFAULT_DOWNLOAD_DIRECTORY,
    VideoDownloadQueuePresenterTestHarness,
    build_progress_snapshot,
    build_selection,
    queue_harness,
)
from videobay_gui.core.media_download_failure import (
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome
from videobay_gui.core.video_download_queue_presenter import (
    DUPLICATE_DOWNLOAD_ALREADY_QUEUED_NOTICE,
)
from videobay_gui.core.videobay_user_settings import OutputDirectoryProblem

__all__ = ["queue_harness"]
EXECUTIONS_AFTER_ONE_RETRY = 2


def test_initial_state_shows_saved_output_directory(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.queue_presenter.present_initial_download_state()

    assert queue_harness.queue_view_fake.shown_output_directories == [DEFAULT_DOWNLOAD_DIRECTORY]


def test_choosing_valid_directory_saves_settings_and_shows_it(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.queue_presenter.handle_output_directory_chosen("/media/hd/videos")

    assert (
        queue_harness.settings_store_fake.stored_videobay_user_settings.preferred_output_directory
        == "/media/hd/videos"
    )
    assert queue_harness.queue_view_fake.shown_output_directories == ["/media/hd/videos"]


@pytest.mark.parametrize("cancelled_dialog_path", ["", "   "])
def test_cancelled_folder_dialog_changes_nothing(
    queue_harness: VideoDownloadQueuePresenterTestHarness, cancelled_dialog_path: str
):
    queue_harness.queue_presenter.handle_output_directory_chosen(cancelled_dialog_path)

    assert queue_harness.settings_store_fake.save_call_count == 0
    assert queue_harness.queue_view_fake.shown_output_directories == []


def test_ec06_choosing_unwritable_directory_is_rejected(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.output_directory_probe_fake.output_directory_problems_by_path["/root"] = (
        OutputDirectoryProblem.OUTPUT_DIRECTORY_NOT_WRITABLE
    )

    queue_harness.queue_presenter.handle_output_directory_chosen("/root")

    assert queue_harness.settings_store_fake.save_call_count == 0
    assert "/root" in str(queue_harness.queue_view_fake.shown_download_notices[-1])


def test_cancelling_a_queued_job_cancels_it_without_running_it(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    for video_identifier in ("a", "b", "c"):
        queue_harness.request_selection(build_selection(video_identifier))

    queue_harness.queue_presenter.handle_video_download_job_cancel_requested(3)
    queue_harness.worker_pool_fake.drain_pending_background_tasks()
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    assert queue_harness.queue_view_fake.latest_row_of_job(3).job_status_label == "Cancelado"
    assert "https://youtu.be/c" not in queue_harness.executed_media_urls()


def test_ec09_cancelling_a_running_job_stops_it_and_starts_the_next(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.download_executor_fake.scripted_progress_snapshots = [build_progress_snapshot(5)]
    for video_identifier in ("a", "b", "c"):
        queue_harness.request_selection(build_selection(video_identifier))

    queue_harness.queue_presenter.handle_video_download_job_cancel_requested(1)
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    assert queue_harness.queue_view_fake.latest_row_of_job(1).job_status_label == "Cancelado"
    assert "5%" not in queue_harness.queue_view_fake.status_labels_of_job(1)
    assert queue_harness.queue_view_fake.latest_row_of_job(3).job_status_label == "Iniciando…"


def test_retry_runs_a_failed_job_again_with_the_same_options(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.download_executor_fake.scripted_download_error = MediaDownloadFailedError(
        MediaDownloadFailureKind.NETWORK_UNREACHABLE, "reset"
    )
    queue_harness.request_selection(build_selection())
    queue_harness.worker_pool_fake.drain_pending_background_tasks()
    queue_harness.download_executor_fake.scripted_download_error = None

    queue_harness.queue_presenter.handle_video_download_job_retry_requested(1)
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    executed_downloads = queue_harness.download_executor_fake.executed_downloads
    assert len(executed_downloads) == EXECUTIONS_AFTER_ONE_RETRY
    assert executed_downloads[1] == executed_downloads[0]
    assert queue_harness.queue_view_fake.latest_row_of_job(1).job_status_label == "Concluído"


def test_ec10_retry_that_would_duplicate_an_active_job_shows_notice(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.download_executor_fake.scripted_download_error = RuntimeError("boom")
    queue_harness.request_selection(build_selection())
    queue_harness.worker_pool_fake.drain_pending_background_tasks()
    queue_harness.request_selection(build_selection())

    queue_harness.queue_presenter.handle_video_download_job_retry_requested(1)

    assert queue_harness.queue_view_fake.shown_download_notices[-1] == (
        DUPLICATE_DOWNLOAD_ALREADY_QUEUED_NOTICE
    )
    assert queue_harness.queue_view_fake.latest_row_of_job(1).job_status_label == "Falhou"


def test_progress_rendered_after_the_job_finished_does_not_overwrite_the_final_row(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(build_selection())
    queue_presenter = queue_harness.queue_presenter
    queue_presenter.forward_job_progress_from_worker_thread(1, build_progress_snapshot(50))
    queue_presenter.handle_job_download_finished(1, MediaDownloadOutcome(("/d/a.mp4",), False))

    queue_presenter.render_latest_job_progress_on_ui_thread(1)

    assert queue_harness.queue_view_fake.latest_row_of_job(1).job_status_label == "Concluído"


def test_ec09_progress_rendered_after_cancel_request_is_dropped(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(build_selection())
    queue_presenter = queue_harness.queue_presenter
    queue_presenter.forward_job_progress_from_worker_thread(1, build_progress_snapshot(50))
    queue_presenter.handle_video_download_job_cancel_requested(1)

    queue_presenter.render_latest_job_progress_on_ui_thread(1)

    assert "50%" not in queue_harness.queue_view_fake.status_labels_of_job(1)


def test_cancelling_a_finished_job_changes_nothing(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(build_selection())
    queue_harness.worker_pool_fake.drain_pending_background_tasks()
    shown_row_count = len(queue_harness.queue_view_fake.shown_job_rows)

    queue_harness.queue_presenter.handle_video_download_job_cancel_requested(1)

    assert len(queue_harness.queue_view_fake.shown_job_rows) == shown_row_count
    assert queue_harness.queue_view_fake.latest_row_of_job(1).job_status_label == "Concluído"
