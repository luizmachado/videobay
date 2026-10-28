import pytest

from videobay_gui.core.media_quality_choice import BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
from videobay_gui.core.video_download_job import (
    InvalidVideoDownloadJobTransitionError,
    VideoDownloadJobStatus,
)
from videobay_gui.core.video_download_job_queue import (
    UnknownVideoDownloadJobError,
    VideoDownloadJobQueue,
)
from videobay_gui.core.video_download_request import VideoDownloadRequest

TWO_CONCURRENT_DOWNLOADS = 2


def build_request_for_video(video_identifier: str) -> VideoDownloadRequest:
    return VideoDownloadRequest(
        f"https://youtu.be/{video_identifier}", BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, "/downloads"
    )


def build_queue_with_videos(*video_identifiers: str) -> VideoDownloadJobQueue:
    video_download_job_queue = VideoDownloadJobQueue(TWO_CONCURRENT_DOWNLOADS)
    for video_identifier in video_identifiers:
        video_download_job_queue.enqueue_video_download_request(
            build_request_for_video(video_identifier)
        )
    return video_download_job_queue


def statuses_in_queue_order(
    video_download_job_queue: VideoDownloadJobQueue,
) -> list[VideoDownloadJobStatus]:
    return [
        video_download_job.video_download_job_status
        for video_download_job in video_download_job_queue.list_video_download_jobs()
    ]


def test_enqueue_assigns_increasing_identifiers_and_queued_status():
    video_download_job_queue = VideoDownloadJobQueue(TWO_CONCURRENT_DOWNLOADS)

    first_job = video_download_job_queue.enqueue_video_download_request(
        build_request_for_video("a")
    )
    second_job = video_download_job_queue.enqueue_video_download_request(
        build_request_for_video("b")
    )

    assert (first_job.video_download_job_identifier, second_job.video_download_job_identifier) == (
        1,
        2,
    )
    assert statuses_in_queue_order(video_download_job_queue) == [VideoDownloadJobStatus.QUEUED] * 2


def test_claim_starts_jobs_in_arrival_order_up_to_the_limit():
    video_download_job_queue = build_queue_with_videos("a", "b", "c")

    claimed_jobs = video_download_job_queue.claim_video_download_jobs_ready_to_start()

    assert [job.video_download_job_identifier for job in claimed_jobs] == [1, 2]
    assert statuses_in_queue_order(video_download_job_queue) == [
        VideoDownloadJobStatus.RUNNING,
        VideoDownloadJobStatus.RUNNING,
        VideoDownloadJobStatus.QUEUED,
    ]
    assert video_download_job_queue.claim_video_download_jobs_ready_to_start() == []


@pytest.mark.parametrize(
    "finishing_status",
    [
        VideoDownloadJobStatus.COMPLETED,
        VideoDownloadJobStatus.FAILED,
        VideoDownloadJobStatus.CANCELLED,
    ],
)
def test_finishing_a_running_job_frees_a_slot_for_the_next_one(
    finishing_status: VideoDownloadJobStatus,
):
    video_download_job_queue = build_queue_with_videos("a", "b", "c")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()

    video_download_job_queue.record_video_download_job_outcome(1, finishing_status)

    claimed_jobs = video_download_job_queue.claim_video_download_jobs_ready_to_start()
    assert [job.video_download_job_identifier for job in claimed_jobs] == [3]
    assert video_download_job_queue.find_video_download_job(1).video_download_job_status is (
        finishing_status
    )


def test_raising_the_limit_lets_more_jobs_start():
    video_download_job_queue = build_queue_with_videos("a", "b", "c", "d")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()

    video_download_job_queue.change_maximum_concurrent_downloads(3)

    claimed_jobs = video_download_job_queue.claim_video_download_jobs_ready_to_start()
    assert [job.video_download_job_identifier for job in claimed_jobs] == [3]


def test_recording_an_outcome_for_a_job_that_never_started_is_rejected():
    video_download_job_queue = build_queue_with_videos("a")

    with pytest.raises(InvalidVideoDownloadJobTransitionError):
        video_download_job_queue.record_video_download_job_outcome(
            1, VideoDownloadJobStatus.COMPLETED
        )


def test_unknown_job_identifier_is_reported_explicitly():
    with pytest.raises(UnknownVideoDownloadJobError, match="42"):
        build_queue_with_videos("a").find_video_download_job(42)


def test_lowering_the_limit_below_running_jobs_starts_nothing_and_stops_nothing():
    video_download_job_queue = build_queue_with_videos("a", "b", "c")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()

    video_download_job_queue.change_maximum_concurrent_downloads(1)

    assert video_download_job_queue.claim_video_download_jobs_ready_to_start() == []
    assert statuses_in_queue_order(video_download_job_queue) == [
        VideoDownloadJobStatus.RUNNING,
        VideoDownloadJobStatus.RUNNING,
        VideoDownloadJobStatus.QUEUED,
    ]
