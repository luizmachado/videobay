from dataclasses import dataclass
from enum import StrEnum

from videobay_gui.core.download_progress_snapshot import (
    DownloadProgressSnapshot,
    build_download_progress_view_model,
)
from videobay_gui.core.video_download_job import VideoDownloadJob, VideoDownloadJobStatus

FINISHED_JOB_STATUS_LABELS = {
    VideoDownloadJobStatus.QUEUED: "Na fila",
    VideoDownloadJobStatus.COMPLETED: "Concluído",
    VideoDownloadJobStatus.FAILED: "Falhou",
    VideoDownloadJobStatus.CANCELLED: "Cancelado",
}
RUNNING_WITHOUT_PROGRESS_LABEL = "Iniciando…"


class VideoDownloadJobRowTone(StrEnum):
    NEUTRAL = "neutral"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class VideoDownloadJobRowViewModel:
    video_download_job_identifier: int
    media_display_title_label: str
    job_status_label: str
    job_detail_label: str
    progress_bar_fraction: float | None
    is_progress_indeterminate: bool
    can_cancel_video_download_job: bool
    can_retry_video_download_job: bool
    job_row_tone: VideoDownloadJobRowTone


def build_video_download_job_row_view_model(
    video_download_job: VideoDownloadJob,
    latest_progress_snapshot: DownloadProgressSnapshot | None,
    job_outcome_message: str | None,
    failed_job_is_retryable: bool = True,
) -> VideoDownloadJobRowViewModel:
    job_status = video_download_job.video_download_job_status
    job_status_label, job_detail_label, progress_bar_fraction = build_job_status_texts(
        job_status, latest_progress_snapshot, job_outcome_message
    )
    return VideoDownloadJobRowViewModel(
        video_download_job_identifier=video_download_job.video_download_job_identifier,
        media_display_title_label=video_download_job.media_display_title.strip()
        or video_download_job.video_download_request.media_url,
        job_status_label=job_status_label,
        job_detail_label=job_detail_label,
        progress_bar_fraction=progress_bar_fraction,
        # WHY: EC-08. A running job without a known total animates instead of showing 0%.
        is_progress_indeterminate=job_status is VideoDownloadJobStatus.RUNNING
        and progress_bar_fraction is None,
        can_cancel_video_download_job=video_download_job.is_video_download_job_active,
        can_retry_video_download_job=job_status is VideoDownloadJobStatus.CANCELLED
        or (job_status is VideoDownloadJobStatus.FAILED and failed_job_is_retryable),
        job_row_tone=(
            VideoDownloadJobRowTone.SUCCESS
            if job_status is VideoDownloadJobStatus.COMPLETED
            else VideoDownloadJobRowTone.FAILURE
            if job_status is VideoDownloadJobStatus.FAILED
            else VideoDownloadJobRowTone.NEUTRAL
        ),
    )


def build_job_status_texts(
    job_status: VideoDownloadJobStatus,
    latest_progress_snapshot: DownloadProgressSnapshot | None,
    job_outcome_message: str | None,
) -> tuple[str, str, float | None]:
    if job_status is not VideoDownloadJobStatus.RUNNING:
        finished_fraction = 1.0 if job_status is VideoDownloadJobStatus.COMPLETED else None
        return (
            FINISHED_JOB_STATUS_LABELS[job_status],
            job_outcome_message or "",
            finished_fraction,
        )
    if latest_progress_snapshot is None:
        return RUNNING_WITHOUT_PROGRESS_LABEL, "", None
    progress_view_model = build_download_progress_view_model(latest_progress_snapshot)
    progress_details = (
        progress_view_model.progress_size_label,
        progress_view_model.progress_speed_label,
        progress_view_model.progress_remaining_time_label,
    )
    return (
        progress_view_model.progress_percentage_label,
        "   ".join(progress_detail for progress_detail in progress_details if progress_detail),
        progress_view_model.progress_bar_fraction,
    )
