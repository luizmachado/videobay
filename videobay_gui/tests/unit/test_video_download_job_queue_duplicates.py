import pytest

from tests.unit.test_video_download_job_queue import (
    build_queue_with_videos,
    build_request_for_video,
)
from videobay_gui.core.media_quality_choice import MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE
from videobay_gui.core.video_download_job import VideoDownloadJobStatus
from videobay_gui.core.video_download_job_queue import DuplicateVideoDownloadRequestError
from videobay_gui.core.video_download_request import VideoDownloadRequest


@pytest.mark.parametrize("duplicated_job_is_running", [False, True])
def test_ec10_same_request_while_active_is_rejected(duplicated_job_is_running: bool):
    video_download_job_queue = build_queue_with_videos("a")
    if duplicated_job_is_running:
        video_download_job_queue.claim_video_download_jobs_ready_to_start()

    with pytest.raises(DuplicateVideoDownloadRequestError):
        video_download_job_queue.enqueue_video_download_request(build_request_for_video("a"))

    assert len(video_download_job_queue.list_video_download_jobs()) == 1


def test_ec10_same_url_with_different_options_is_a_different_download():
    video_download_job_queue = build_queue_with_videos("a")
    audio_request_for_same_video = VideoDownloadRequest(
        build_request_for_video("a").media_url, MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE, "/downloads"
    )

    video_download_job_queue.enqueue_video_download_request(audio_request_for_same_video)

    assert len(video_download_job_queue.list_video_download_jobs()) == 2  # noqa: PLR2004


@pytest.mark.parametrize(
    "finished_status",
    [
        VideoDownloadJobStatus.COMPLETED,
        VideoDownloadJobStatus.FAILED,
        VideoDownloadJobStatus.CANCELLED,
    ],
)
def test_ec10_finished_jobs_do_not_block_downloading_again(
    finished_status: VideoDownloadJobStatus,
):
    video_download_job_queue = build_queue_with_videos("a")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()
    video_download_job_queue.record_video_download_job_outcome(1, finished_status)

    video_download_job_queue.enqueue_video_download_request(build_request_for_video("a"))

    assert len(video_download_job_queue.list_video_download_jobs()) == 2  # noqa: PLR2004


def test_ec10_retry_is_rejected_when_an_identical_job_is_already_active():
    video_download_job_queue = build_queue_with_videos("a")
    video_download_job_queue.claim_video_download_jobs_ready_to_start()
    video_download_job_queue.record_video_download_job_outcome(1, VideoDownloadJobStatus.FAILED)
    video_download_job_queue.enqueue_video_download_request(build_request_for_video("a"))

    with pytest.raises(DuplicateVideoDownloadRequestError):
        video_download_job_queue.retry_video_download_job(1)

    assert video_download_job_queue.find_video_download_job(1).video_download_job_status is (
        VideoDownloadJobStatus.FAILED
    )
