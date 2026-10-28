from tests.unit.video_download_queue_presenter_harness import (
    VideoDownloadQueuePresenterTestHarness,
    build_progress_snapshot,
    build_selection,
    queue_harness,
)

__all__ = ["queue_harness"]
ACTIVE_JOBS_WHEN_TWO_RUN_AND_ONE_WAITS = 3


def test_closing_without_active_downloads_closes_without_asking(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(build_selection())
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    assert queue_harness.queue_presenter.handle_main_window_close_requested() is True
    assert queue_harness.queue_view_fake.asked_close_confirmation_counts == []


def test_ec16_declining_the_confirmation_keeps_window_and_downloads(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    for video_identifier in ("a", "b", "c"):
        queue_harness.request_selection(build_selection(video_identifier))
    queue_harness.queue_view_fake.scripted_close_confirmation_answer = False

    should_close_main_window = queue_harness.queue_presenter.handle_main_window_close_requested()

    assert should_close_main_window is False
    assert queue_harness.queue_view_fake.asked_close_confirmation_counts == [
        ACTIVE_JOBS_WHEN_TWO_RUN_AND_ONE_WAITS
    ]
    assert queue_harness.queue_view_fake.latest_row_of_job(3).job_status_label == "Na fila"


def test_ec16_confirming_cancels_queued_jobs_and_stops_running_ones(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.download_executor_fake.scripted_progress_snapshots = [build_progress_snapshot(5)]
    for video_identifier in ("a", "b", "c"):
        queue_harness.request_selection(build_selection(video_identifier))

    should_close_main_window = queue_harness.queue_presenter.handle_main_window_close_requested()
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    assert should_close_main_window is True
    assert [
        queue_harness.queue_view_fake.latest_row_of_job(job_identifier).job_status_label
        for job_identifier in (1, 2, 3)
    ] == ["Cancelado"] * 3
    assert "https://youtu.be/c" not in queue_harness.executed_media_urls()
