import itertools

import pytest

from videobay_gui.core.media_quality_choice import BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
from videobay_gui.core.video_download_job import (
    ALLOWED_VIDEO_DOWNLOAD_JOB_TRANSITIONS,
    InvalidVideoDownloadJobTransitionError,
    VideoDownloadJob,
    VideoDownloadJobStatus,
)
from videobay_gui.core.video_download_request import VideoDownloadRequest

SAMPLE_VIDEO_DOWNLOAD_REQUEST = VideoDownloadRequest(
    "https://youtu.be/abc", BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, "/home/user/Downloads"
)

EXPECTED_ALLOWED_TRANSITIONS = {
    (VideoDownloadJobStatus.QUEUED, VideoDownloadJobStatus.RUNNING),
    (VideoDownloadJobStatus.QUEUED, VideoDownloadJobStatus.CANCELLED),
    (VideoDownloadJobStatus.RUNNING, VideoDownloadJobStatus.COMPLETED),
    (VideoDownloadJobStatus.RUNNING, VideoDownloadJobStatus.FAILED),
    (VideoDownloadJobStatus.RUNNING, VideoDownloadJobStatus.CANCELLED),
    (VideoDownloadJobStatus.FAILED, VideoDownloadJobStatus.QUEUED),
    (VideoDownloadJobStatus.CANCELLED, VideoDownloadJobStatus.QUEUED),
}


def build_job_in_status(video_download_job_status: VideoDownloadJobStatus) -> VideoDownloadJob:
    return VideoDownloadJob(7, SAMPLE_VIDEO_DOWNLOAD_REQUEST, video_download_job_status)


def test_new_job_starts_queued_and_active():
    new_video_download_job = VideoDownloadJob(1, SAMPLE_VIDEO_DOWNLOAD_REQUEST)

    assert new_video_download_job.video_download_job_status is VideoDownloadJobStatus.QUEUED
    assert new_video_download_job.is_video_download_job_active


@pytest.mark.parametrize(("current_status", "next_status"), sorted(EXPECTED_ALLOWED_TRANSITIONS))
def test_allowed_transitions_return_a_new_job_in_the_next_status(
    current_status: VideoDownloadJobStatus, next_status: VideoDownloadJobStatus
):
    original_job = build_job_in_status(current_status)

    transitioned_job = original_job.transition_video_download_job_to(next_status)

    assert transitioned_job.video_download_job_status is next_status
    assert (
        transitioned_job.video_download_job_identifier == original_job.video_download_job_identifier
    )
    assert original_job.video_download_job_status is current_status


@pytest.mark.parametrize(
    ("current_status", "next_status"),
    sorted(set(itertools.product(VideoDownloadJobStatus, repeat=2)) - EXPECTED_ALLOWED_TRANSITIONS),
)
def test_every_other_transition_is_rejected(
    current_status: VideoDownloadJobStatus, next_status: VideoDownloadJobStatus
):
    with pytest.raises(InvalidVideoDownloadJobTransitionError, match=current_status.value):
        build_job_in_status(current_status).transition_video_download_job_to(next_status)


def test_transition_table_matches_the_documented_state_machine():
    assert {
        (current_status, next_status)
        for current_status, next_statuses in ALLOWED_VIDEO_DOWNLOAD_JOB_TRANSITIONS.items()
        for next_status in next_statuses
    } == EXPECTED_ALLOWED_TRANSITIONS


@pytest.mark.parametrize(
    ("video_download_job_status", "expected_active"),
    [
        (VideoDownloadJobStatus.QUEUED, True),
        (VideoDownloadJobStatus.RUNNING, True),
        (VideoDownloadJobStatus.COMPLETED, False),
        (VideoDownloadJobStatus.FAILED, False),
        (VideoDownloadJobStatus.CANCELLED, False),
    ],
)
def test_only_queued_and_running_jobs_are_active(
    video_download_job_status: VideoDownloadJobStatus, expected_active: bool
):
    assert build_job_in_status(video_download_job_status).is_video_download_job_active is (
        expected_active
    )
