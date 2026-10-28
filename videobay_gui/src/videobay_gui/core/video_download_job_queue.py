from enum import StrEnum

from videobay_gui.core.video_download_job import VideoDownloadJob, VideoDownloadJobStatus
from videobay_gui.core.video_download_request import VideoDownloadRequest


class UnknownVideoDownloadJobError(KeyError):
    pass


class VideoDownloadJobCancellationEffect(StrEnum):
    CANCELLED_BEFORE_START = "cancelled_before_start"
    STOP_RUNNING_DOWNLOAD_REQUESTED = "stop_running_download_requested"
    NOTHING_TO_CANCEL = "nothing_to_cancel"


class VideoDownloadJobQueue:
    """Ordered jobs plus the concurrency rule. Pure state: starting a job is the presenter's job.

    PROVENANCE: ADR-0004 (download concurrency limit, default 2 from VideobayUserSettings).
    """

    def __init__(self, maximum_concurrent_downloads: int) -> None:
        self.maximum_concurrent_downloads = maximum_concurrent_downloads
        # WHY: dicts keep insertion order, which is the FIFO order shown in the queue view.
        self.video_download_jobs_by_identifier: dict[int, VideoDownloadJob] = {}
        self.last_assigned_video_download_job_identifier = 0

    def enqueue_video_download_request(
        self, video_download_request: VideoDownloadRequest
    ) -> VideoDownloadJob:
        self.last_assigned_video_download_job_identifier += 1
        new_video_download_job = VideoDownloadJob(
            self.last_assigned_video_download_job_identifier, video_download_request
        )
        self.store_video_download_job(new_video_download_job)
        return new_video_download_job

    def claim_video_download_jobs_ready_to_start(self) -> list[VideoDownloadJob]:
        free_download_slot_count = self.maximum_concurrent_downloads - self.count_running_jobs()
        queued_jobs_in_arrival_order = [
            video_download_job
            for video_download_job in self.video_download_jobs_by_identifier.values()
            if video_download_job.video_download_job_status is VideoDownloadJobStatus.QUEUED
        ]
        claimed_jobs = [
            queued_job.transition_video_download_job_to(VideoDownloadJobStatus.RUNNING)
            for queued_job in queued_jobs_in_arrival_order[: max(free_download_slot_count, 0)]
        ]
        for claimed_job in claimed_jobs:
            self.store_video_download_job(claimed_job)
        return claimed_jobs

    def record_video_download_job_outcome(
        self, video_download_job_identifier: int, finishing_status: VideoDownloadJobStatus
    ) -> None:
        self.store_video_download_job(
            self.find_video_download_job(
                video_download_job_identifier
            ).transition_video_download_job_to(finishing_status)
        )

    def cancel_video_download_job(
        self, video_download_job_identifier: int
    ) -> VideoDownloadJobCancellationEffect:
        video_download_job = self.find_video_download_job(video_download_job_identifier)
        job_status = video_download_job.video_download_job_status
        if job_status is VideoDownloadJobStatus.QUEUED:
            self.store_video_download_job(
                video_download_job.transition_video_download_job_to(
                    VideoDownloadJobStatus.CANCELLED
                )
            )
            return VideoDownloadJobCancellationEffect.CANCELLED_BEFORE_START
        if job_status is VideoDownloadJobStatus.RUNNING:
            # WHY: the job stays RUNNING until the executor confirms the stop; marking it cancelled
            # now would free its slot while yt-dlp is still writing to disk.
            return VideoDownloadJobCancellationEffect.STOP_RUNNING_DOWNLOAD_REQUESTED
        return VideoDownloadJobCancellationEffect.NOTHING_TO_CANCEL

    def retry_video_download_job(self, video_download_job_identifier: int) -> VideoDownloadJob:
        retried_job = self.find_video_download_job(
            video_download_job_identifier
        ).transition_video_download_job_to(VideoDownloadJobStatus.QUEUED)
        self.store_video_download_job(retried_job)
        return retried_job

    def change_maximum_concurrent_downloads(self, maximum_concurrent_downloads: int) -> None:
        self.maximum_concurrent_downloads = maximum_concurrent_downloads

    def find_video_download_job(self, video_download_job_identifier: int) -> VideoDownloadJob:
        if video_download_job_identifier not in self.video_download_jobs_by_identifier:
            raise UnknownVideoDownloadJobError(video_download_job_identifier)
        return self.video_download_jobs_by_identifier[video_download_job_identifier]

    def list_video_download_jobs(self) -> tuple[VideoDownloadJob, ...]:
        return tuple(self.video_download_jobs_by_identifier.values())

    def count_running_jobs(self) -> int:
        return sum(
            1
            for video_download_job in self.video_download_jobs_by_identifier.values()
            if video_download_job.video_download_job_status is VideoDownloadJobStatus.RUNNING
        )

    def store_video_download_job(self, video_download_job: VideoDownloadJob) -> None:
        self.video_download_jobs_by_identifier[video_download_job.video_download_job_identifier] = (
            video_download_job
        )
