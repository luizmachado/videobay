from dataclasses import dataclass, replace
from enum import StrEnum

from videobay_gui.core.video_download_request import VideoDownloadRequest


class VideoDownloadJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# PROVENANCE: ARCHITECTURE.md "Modelo de domínio". queued→cancelled lets the user drop a job
# that never started; failed/cancelled→queued is "tentar de novo". Completed is final.
ALLOWED_VIDEO_DOWNLOAD_JOB_TRANSITIONS: dict[
    VideoDownloadJobStatus, frozenset[VideoDownloadJobStatus]
] = {
    VideoDownloadJobStatus.QUEUED: frozenset(
        {VideoDownloadJobStatus.RUNNING, VideoDownloadJobStatus.CANCELLED}
    ),
    VideoDownloadJobStatus.RUNNING: frozenset(
        {
            VideoDownloadJobStatus.COMPLETED,
            VideoDownloadJobStatus.FAILED,
            VideoDownloadJobStatus.CANCELLED,
        }
    ),
    VideoDownloadJobStatus.COMPLETED: frozenset(),
    VideoDownloadJobStatus.FAILED: frozenset({VideoDownloadJobStatus.QUEUED}),
    VideoDownloadJobStatus.CANCELLED: frozenset({VideoDownloadJobStatus.QUEUED}),
}
ACTIVE_VIDEO_DOWNLOAD_JOB_STATUSES = frozenset(
    {VideoDownloadJobStatus.QUEUED, VideoDownloadJobStatus.RUNNING}
)


class InvalidVideoDownloadJobTransitionError(Exception):
    pass


@dataclass(frozen=True)
class VideoDownloadJob:
    video_download_job_identifier: int
    video_download_request: VideoDownloadRequest
    video_download_job_status: VideoDownloadJobStatus = VideoDownloadJobStatus.QUEUED
    # WHY: the inspected title is only for display; it is not part of the request, so it
    # never affects duplicate detection (EC-10).
    media_display_title: str = ""

    @property
    def is_video_download_job_active(self) -> bool:
        return self.video_download_job_status in ACTIVE_VIDEO_DOWNLOAD_JOB_STATUSES

    def transition_video_download_job_to(
        self, next_video_download_job_status: VideoDownloadJobStatus
    ) -> "VideoDownloadJob":
        allowed_next_statuses = ALLOWED_VIDEO_DOWNLOAD_JOB_TRANSITIONS[
            self.video_download_job_status
        ]
        if next_video_download_job_status not in allowed_next_statuses:
            raise InvalidVideoDownloadJobTransitionError(
                f"job {self.video_download_job_identifier}: "
                f"{self.video_download_job_status.value} -> {next_video_download_job_status.value}"
            )
        return replace(self, video_download_job_status=next_video_download_job_status)
