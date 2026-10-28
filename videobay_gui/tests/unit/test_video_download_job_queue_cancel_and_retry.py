import pytest

from tests.unit.test_video_download_job_queue import build_queue_with_videos
from videobay_gui.core.video_download_job import (
    InvalidVideoDownloadJobTransitionError,
    VideoDownloadJobStatus,
)
from videobay_gui.core.video_download_job_queue import VideoDownloadJobCancellationEffect


def test_cancelling_a_queued_job_cancels_it_immediately():
    video_download_job_queue = build_queue_with_videos("a", "b", "c")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()

    cancellation_effect = video_download_job_queue.cancel_video_download_job(3)

    assert cancellation_effect is VideoDownloadJobCancellationEffect.CANCELLED_BEFORE_START
    assert video_download_job_queue.find_video_download_job(3).video_download_job_status is (
        VideoDownloadJobStatus.CANCELLED
    )


def test_cancelling_a_running_job_asks_to_stop_it_and_waits_for_the_executor():
    video_download_job_queue = build_queue_with_videos("a")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()

    cancellation_effect = video_download_job_queue.cancel_video_download_job(1)

    assert cancellation_effect is VideoDownloadJobCancellationEffect.STOP_RUNNING_DOWNLOAD_REQUESTED
    assert video_download_job_queue.find_video_download_job(1).video_download_job_status is (
        VideoDownloadJobStatus.RUNNING
    )


@pytest.mark.parametrize(
    "finished_status",
    [
        VideoDownloadJobStatus.COMPLETED,
        VideoDownloadJobStatus.FAILED,
        VideoDownloadJobStatus.CANCELLED,
    ],
)
def test_cancelling_a_finished_job_does_nothing(finished_status: VideoDownloadJobStatus):
    video_download_job_queue = build_queue_with_videos("a")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()
    video_download_job_queue.record_video_download_job_outcome(1, finished_status)

    assert video_download_job_queue.cancel_video_download_job(1) is (
        VideoDownloadJobCancellationEffect.NOTHING_TO_CANCEL
    )
    assert video_download_job_queue.find_video_download_job(1).video_download_job_status is (
        finished_status
    )


@pytest.mark.parametrize(
    "retryable_status", [VideoDownloadJobStatus.FAILED, VideoDownloadJobStatus.CANCELLED]
)
def test_retry_puts_failed_or_cancelled_job_back_in_the_queue(
    retryable_status: VideoDownloadJobStatus,
):
    video_download_job_queue = build_queue_with_videos("a")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()
    video_download_job_queue.record_video_download_job_outcome(1, retryable_status)

    retried_job = video_download_job_queue.retry_video_download_job(1)

    assert retried_job.video_download_job_status is VideoDownloadJobStatus.QUEUED
    assert [
        job.video_download_job_identifier
        for job in video_download_job_queue.claim_video_download_jobs_ready_to_start()
    ] == [1]


def test_completed_job_cannot_be_retried():
    video_download_job_queue = build_queue_with_videos("a")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()
    video_download_job_queue.record_video_download_job_outcome(1, VideoDownloadJobStatus.COMPLETED)

    with pytest.raises(InvalidVideoDownloadJobTransitionError):
        video_download_job_queue.retry_video_download_job(1)
