from dataclasses import replace

from tests.unit.video_download_queue_presenter_harness import (
    VideoDownloadQueuePresenterTestHarness,
    build_selection,
    queue_harness,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome
from videobay_gui.core.media_download_selection import NO_PLAYLIST_ITEMS_SELECTED_NOTICE

__all__ = ["queue_harness"]


def test_ec11_playlist_job_downloads_selected_items_and_reports_n_of_m(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.download_executor_fake.scripted_outcome = MediaDownloadOutcome(
        ("/d/PL/1 - Aula 1.mp4",), False
    )

    queue_harness.request_selection(
        replace(
            build_selection(),
            is_playlist_selection=True,
            selected_playlist_item_indices_for_download=(1, 3),
        )
    )
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    executed_options = queue_harness.download_executor_fake.executed_downloads[0][1]
    assert executed_options["playlist_items"] == "1,3"
    assert queue_harness.queue_view_fake.latest_row_of_job(1).job_detail_label == (
        "1 de 2 baixados"
    )


def test_playlist_with_nothing_selected_is_blocked_instead_of_downloading_everything(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(
        replace(
            build_selection(),
            is_playlist_selection=True,
            selected_playlist_item_indices_for_download=(),
        )
    )

    assert queue_harness.queue_view_fake.shown_download_notices == [
        NO_PLAYLIST_ITEMS_SELECTED_NOTICE
    ]
    assert queue_harness.queue_view_fake.shown_job_rows == []
