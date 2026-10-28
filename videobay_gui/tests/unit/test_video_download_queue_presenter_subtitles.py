from dataclasses import replace

from tests.unit.video_download_queue_presenter_harness import (
    VideoDownloadQueuePresenterTestHarness,
    build_selection,
    queue_harness,
)
from videobay_gui.core.media_download_selection import PLAYLIST_SUBTITLES_MAY_BE_MISSING_NOTICE

__all__ = ["queue_harness"]


def test_subtitle_languages_reach_the_executed_options(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(replace(build_selection(), selected_subtitle_languages=("en",)))
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    assert queue_harness.download_executor_fake.executed_downloads[0][1]["subtitleslangs"] == ["en"]


def test_ec13_playlist_with_subtitles_warns_that_some_items_may_lack_them(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(
        replace(
            build_selection(),
            is_playlist_selection=True,
            selected_playlist_item_indices_for_download=(1,),
            selected_subtitle_languages=("pt",),
        )
    )

    assert queue_harness.queue_view_fake.shown_download_notices[-1] == (
        PLAYLIST_SUBTITLES_MAY_BE_MISSING_NOTICE
    )
    assert len(queue_harness.queue_view_fake.shown_job_rows) >= 1
