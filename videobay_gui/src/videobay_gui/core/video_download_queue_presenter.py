import os
from dataclasses import dataclass, replace
from typing import Any

from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_download_failure import (
    MediaDownloadCancelledError,
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
    describe_media_download_failure_for_user,
    is_media_download_failure_retryable,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome
from videobay_gui.core.media_download_selection import MediaDownloadSelection
from videobay_gui.core.video_download_job import VideoDownloadJobStatus
from videobay_gui.core.video_download_job_queue import (
    DuplicateVideoDownloadRequestError,
    VideoDownloadJobCancellationEffect,
    VideoDownloadJobQueue,
)
from videobay_gui.core.video_download_job_row_view_model import (
    build_video_download_job_row_view_model,
)
from videobay_gui.core.video_download_request import VideoDownloadRequest
from videobay_gui.core.videobay_user_settings import describe_output_directory_problem_for_user
from videobay_gui.core.yt_dlp_download_options_builder import (
    build_yt_dlp_download_options,
    find_download_blocking_problem,
)
from videobay_gui.ports.background_worker_pool_port import BackgroundWorkerPoolPort
from videobay_gui.ports.ffmpeg_availability_probe_port import FfmpegAvailabilityProbePort
from videobay_gui.ports.media_download_executor_port import MediaDownloadExecutorPort
from videobay_gui.ports.output_directory_access_probe_port import OutputDirectoryAccessProbePort
from videobay_gui.ports.video_download_queue_view_port import VideoDownloadQueueViewPort
from videobay_gui.ports.videobay_settings_store_port import VideobaySettingsStorePort

NO_INSPECTED_MEDIA_TO_DOWNLOAD_NOTICE = "Busque um vídeo antes de baixar."
DUPLICATE_DOWNLOAD_ALREADY_QUEUED_NOTICE = "Esse download já está na fila."


@dataclass(frozen=True)
class VideoDownloadQueuePorts:
    media_download_executor: MediaDownloadExecutorPort
    background_worker_pool: BackgroundWorkerPoolPort
    videobay_settings_store: VideobaySettingsStorePort
    output_directory_access_probe: OutputDirectoryAccessProbePort
    ffmpeg_availability_probe: FfmpegAvailabilityProbePort


class VideoDownloadQueuePresenter:
    """Adds inspected media to the queue and runs up to N downloads at once (F-04, ADR-0004)."""

    def __init__(
        self, queue_view: VideoDownloadQueueViewPort, queue_ports: VideoDownloadQueuePorts
    ) -> None:
        self.queue_view = queue_view
        self.queue_ports = queue_ports
        self.video_download_job_queue = VideoDownloadJobQueue(
            queue_ports.videobay_settings_store.load_videobay_user_settings().maximum_concurrent_downloads
        )
        self.yt_dlp_options_by_job: dict[int, dict[str, Any]] = {}
        self.outcome_messages_by_job: dict[int, str] = {}
        self.retryable_failure_by_job: dict[int, bool] = {}
        self.cancellation_requested_jobs: set[int] = set()
        self.latest_unrendered_progress_by_job: dict[int, DownloadProgressSnapshot] = {}
        self.progress_render_scheduled_jobs: set[int] = set()

    def present_initial_download_state(self) -> None:
        self.queue_view.show_output_directory(self.load_preferred_output_directory())

    def load_preferred_output_directory(self) -> str:
        settings_store = self.queue_ports.videobay_settings_store
        return settings_store.load_videobay_user_settings().preferred_output_directory

    def handle_output_directory_chosen(self, chosen_output_directory: str) -> None:
        normalized_output_directory = chosen_output_directory.strip()
        # WHY: Tk's folder dialog returns "" when the user presses Cancel.
        if not normalized_output_directory:
            return
        if not self.show_output_directory_problem_if_any(normalized_output_directory):
            return
        settings_store = self.queue_ports.videobay_settings_store
        settings_store.save_videobay_user_settings(
            replace(
                settings_store.load_videobay_user_settings(),
                preferred_output_directory=normalized_output_directory,
            )
        )
        self.queue_view.show_output_directory(normalized_output_directory)

    def show_output_directory_problem_if_any(self, output_directory: str) -> bool:
        output_directory_problem = (
            self.queue_ports.output_directory_access_probe.find_output_directory_problem(
                output_directory
            )
        )
        if output_directory_problem is None:
            return True
        self.queue_view.show_download_notice(
            describe_output_directory_problem_for_user(output_directory_problem, output_directory)
        )
        return False

    def handle_download_requested_for_selection(
        self, media_download_selection: MediaDownloadSelection | None
    ) -> None:
        if media_download_selection is None:
            self.queue_view.show_download_notice(NO_INSPECTED_MEDIA_TO_DOWNLOAD_NOTICE)
            return
        output_directory = self.load_preferred_output_directory()
        # WHY: the folder may have been unmounted or deleted since it was chosen (EC-06).
        if not self.show_output_directory_problem_if_any(output_directory):
            return
        video_download_request = VideoDownloadRequest(
            media_download_selection.media_url,
            media_download_selection.media_quality_choice,
            output_directory,
        )
        is_ffmpeg_available = (
            self.queue_ports.ffmpeg_availability_probe.is_ffmpeg_executable_available()
        )
        download_blocking_problem = find_download_blocking_problem(
            video_download_request, is_ffmpeg_available
        )
        if download_blocking_problem is not None:
            self.queue_view.show_download_notice(download_blocking_problem)
            return
        self.enqueue_and_start(
            video_download_request, media_download_selection, is_ffmpeg_available
        )

    def enqueue_and_start(
        self,
        video_download_request: VideoDownloadRequest,
        media_download_selection: MediaDownloadSelection,
        is_ffmpeg_available: bool,
    ) -> None:
        try:
            new_job = self.video_download_job_queue.enqueue_video_download_request(
                video_download_request, media_download_selection.media_display_title
            )
        except DuplicateVideoDownloadRequestError:
            self.queue_view.show_download_notice(DUPLICATE_DOWNLOAD_ALREADY_QUEUED_NOTICE)
            return
        download_options_build_result = build_yt_dlp_download_options(
            video_download_request, is_ffmpeg_available
        )
        new_job_identifier = new_job.video_download_job_identifier
        self.yt_dlp_options_by_job[new_job_identifier] = (
            download_options_build_result.yt_dlp_download_options
        )
        self.queue_view.show_download_notice(download_options_build_result.ffmpeg_fallback_notice)
        self.show_job_row(new_job_identifier)
        self.start_jobs_with_free_slots()

    def start_jobs_with_free_slots(self) -> None:
        for claimed_job in self.video_download_job_queue.claim_video_download_jobs_ready_to_start():
            self.start_claimed_job(claimed_job.video_download_job_identifier)

    def start_claimed_job(self, job_identifier: int) -> None:
        self.show_job_row(job_identifier)
        media_url = self.video_download_job_queue.find_video_download_job(
            job_identifier
        ).video_download_request.media_url
        self.queue_ports.background_worker_pool.submit_background_task(
            lambda: self.queue_ports.media_download_executor.execute_media_download(
                media_url,
                self.yt_dlp_options_by_job[job_identifier],
                lambda snapshot: self.forward_job_progress_from_worker_thread(
                    job_identifier, snapshot
                ),
                lambda: job_identifier in self.cancellation_requested_jobs,
            ),
            lambda outcome: self.handle_job_download_finished(job_identifier, outcome),
            lambda error: self.handle_job_download_failed(job_identifier, error),
        )

    def forward_job_progress_from_worker_thread(
        self, job_identifier: int, download_progress_snapshot: DownloadProgressSnapshot
    ) -> None:
        # WHY: yt-dlp fires hooks many times per second; only the newest snapshot is drawn
        # and at most one render per job waits in the UI queue at any time.
        self.latest_unrendered_progress_by_job[job_identifier] = download_progress_snapshot
        if job_identifier in self.progress_render_scheduled_jobs:
            return
        self.progress_render_scheduled_jobs.add(job_identifier)
        self.queue_ports.background_worker_pool.post_callback_to_ui_thread(
            lambda: self.render_latest_job_progress_on_ui_thread(job_identifier)
        )

    def render_latest_job_progress_on_ui_thread(self, job_identifier: int) -> None:
        self.progress_render_scheduled_jobs.discard(job_identifier)
        job_status = self.video_download_job_queue.find_video_download_job(
            job_identifier
        ).video_download_job_status
        # WHY: progress posted just before a cancel or the finish must not overwrite that state.
        if job_status is not VideoDownloadJobStatus.RUNNING:
            return
        if job_identifier in self.cancellation_requested_jobs:
            return
        self.show_job_row(job_identifier, self.latest_unrendered_progress_by_job[job_identifier])

    def handle_job_download_finished(
        self, job_identifier: int, media_download_outcome: MediaDownloadOutcome
    ) -> None:
        downloaded_file_name = (
            os.path.basename(media_download_outcome.downloaded_file_paths[0])
            if media_download_outcome.downloaded_file_paths
            else ""
        )
        self.outcome_messages_by_job[job_identifier] = (
            f"Já baixado: {downloaded_file_name}"
            if media_download_outcome.was_already_downloaded
            else downloaded_file_name
        )
        self.finish_job(job_identifier, VideoDownloadJobStatus.COMPLETED)

    def handle_job_download_failed(
        self, job_identifier: int, media_download_error: Exception
    ) -> None:
        if isinstance(media_download_error, MediaDownloadCancelledError):
            self.finish_job(job_identifier, VideoDownloadJobStatus.CANCELLED)
            return
        media_download_failure_kind = (
            media_download_error.media_download_failure_kind
            if isinstance(media_download_error, MediaDownloadFailedError)
            else MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE
        )
        self.outcome_messages_by_job[job_identifier] = describe_media_download_failure_for_user(
            media_download_failure_kind
        )
        self.retryable_failure_by_job[job_identifier] = is_media_download_failure_retryable(
            media_download_failure_kind
        )
        self.finish_job(job_identifier, VideoDownloadJobStatus.FAILED)

    def finish_job(self, job_identifier: int, finishing_status: VideoDownloadJobStatus) -> None:
        self.video_download_job_queue.record_video_download_job_outcome(
            job_identifier, finishing_status
        )
        self.show_job_row(job_identifier)
        self.start_jobs_with_free_slots()

    def handle_video_download_job_cancel_requested(
        self, video_download_job_identifier: int
    ) -> None:
        cancellation_effect = self.video_download_job_queue.cancel_video_download_job(
            video_download_job_identifier
        )
        if cancellation_effect is VideoDownloadJobCancellationEffect.CANCELLED_BEFORE_START:
            self.show_job_row(video_download_job_identifier)
            return
        if (
            cancellation_effect
            is VideoDownloadJobCancellationEffect.STOP_RUNNING_DOWNLOAD_REQUESTED
        ):
            self.cancellation_requested_jobs.add(video_download_job_identifier)

    def handle_video_download_job_retry_requested(self, video_download_job_identifier: int) -> None:
        try:
            self.video_download_job_queue.retry_video_download_job(video_download_job_identifier)
        except DuplicateVideoDownloadRequestError:
            self.queue_view.show_download_notice(DUPLICATE_DOWNLOAD_ALREADY_QUEUED_NOTICE)
            return
        self.cancellation_requested_jobs.discard(video_download_job_identifier)
        self.outcome_messages_by_job.pop(video_download_job_identifier, None)
        self.show_job_row(video_download_job_identifier)
        self.start_jobs_with_free_slots()

    def handle_main_window_close_requested(self) -> bool:
        active_job_identifiers = [
            video_download_job.video_download_job_identifier
            for video_download_job in self.video_download_job_queue.list_video_download_jobs()
            if video_download_job.is_video_download_job_active
        ]
        if not active_job_identifiers:
            return True
        if not self.queue_view.confirm_closing_with_active_downloads(len(active_job_identifiers)):
            return False
        # WHY: EC-16. Cancelling (instead of just exiting) lets each running executor remove its
        # .part files; the worker threads then finish before the interpreter exits.
        for active_job_identifier in active_job_identifiers:
            self.handle_video_download_job_cancel_requested(active_job_identifier)
        return True

    def show_job_row(
        self, job_identifier: int, latest_progress_snapshot: DownloadProgressSnapshot | None = None
    ) -> None:
        self.queue_view.show_video_download_job_row(
            build_video_download_job_row_view_model(
                self.video_download_job_queue.find_video_download_job(job_identifier),
                latest_progress_snapshot,
                self.outcome_messages_by_job.get(job_identifier),
                self.retryable_failure_by_job.get(job_identifier, True),
            )
        )
