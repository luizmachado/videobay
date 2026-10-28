import os
from dataclasses import dataclass, replace

from videobay_gui.core.download_progress_snapshot import (
    DownloadProgressSnapshot,
    build_download_progress_view_model,
)
from videobay_gui.core.media_download_failure import (
    MediaDownloadCancelledError,
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
    describe_media_download_failure_for_user,
    is_media_download_failure_retryable,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome
from videobay_gui.core.media_quality_choice import MediaQualityChoice
from videobay_gui.core.video_download_request import VideoDownloadRequest
from videobay_gui.core.videobay_user_settings import describe_output_directory_problem_for_user
from videobay_gui.core.yt_dlp_download_options_builder import build_yt_dlp_download_options
from videobay_gui.ports.background_worker_pool_port import BackgroundWorkerPoolPort
from videobay_gui.ports.ffmpeg_availability_probe_port import FfmpegAvailabilityProbePort
from videobay_gui.ports.media_download_executor_port import MediaDownloadExecutorPort
from videobay_gui.ports.output_directory_access_probe_port import OutputDirectoryAccessProbePort
from videobay_gui.ports.single_media_download_view_port import SingleMediaDownloadViewPort
from videobay_gui.ports.videobay_settings_store_port import VideobaySettingsStorePort

NO_INSPECTED_MEDIA_TO_DOWNLOAD_NOTICE = "Busque um vídeo antes de baixar."


@dataclass(frozen=True)
class SingleMediaDownloadPorts:
    media_download_executor: MediaDownloadExecutorPort
    background_worker_pool: BackgroundWorkerPoolPort
    videobay_settings_store: VideobaySettingsStorePort
    output_directory_access_probe: OutputDirectoryAccessProbePort
    ffmpeg_availability_probe: FfmpegAvailabilityProbePort


class SingleMediaDownloadPresenter:
    """One download at a time (F-02); the queue in F-04 will run several of these flows."""

    def __init__(
        self,
        download_view: SingleMediaDownloadViewPort,
        single_media_download_ports: SingleMediaDownloadPorts,
    ) -> None:
        self.download_view = download_view
        self.media_download_executor = single_media_download_ports.media_download_executor
        self.background_worker_pool = single_media_download_ports.background_worker_pool
        self.videobay_settings_store = single_media_download_ports.videobay_settings_store
        self.output_directory_access_probe = (
            single_media_download_ports.output_directory_access_probe
        )
        self.ffmpeg_availability_probe = single_media_download_ports.ffmpeg_availability_probe
        self.is_download_active = False
        self.is_download_cancellation_requested = False
        self.last_requested_download_target: tuple[str, MediaQualityChoice] | None = None
        self.latest_unrendered_progress_snapshot: DownloadProgressSnapshot | None = None
        self.is_progress_render_scheduled = False

    def present_initial_download_state(self) -> None:
        self.download_view.show_output_directory(
            self.videobay_settings_store.load_videobay_user_settings().preferred_output_directory
        )

    def handle_output_directory_chosen(self, chosen_output_directory: str) -> None:
        normalized_output_directory = chosen_output_directory.strip()
        # WHY: Tk's folder dialog returns "" when the user presses Cancel.
        if not normalized_output_directory:
            return
        if not self.show_output_directory_problem_if_any(normalized_output_directory):
            return
        current_settings = self.videobay_settings_store.load_videobay_user_settings()
        self.videobay_settings_store.save_videobay_user_settings(
            replace(current_settings, preferred_output_directory=normalized_output_directory)
        )
        self.download_view.show_output_directory(normalized_output_directory)

    def show_output_directory_problem_if_any(self, output_directory: str) -> bool:
        output_directory_problem = self.output_directory_access_probe.find_output_directory_problem(
            output_directory
        )
        if output_directory_problem is None:
            return True
        self.download_view.show_download_notice(
            describe_output_directory_problem_for_user(output_directory_problem, output_directory)
        )
        return False

    def handle_download_requested(
        self, media_url: str, media_quality_choice: MediaQualityChoice
    ) -> None:
        if self.is_download_active:
            return
        output_directory = (
            self.videobay_settings_store.load_videobay_user_settings().preferred_output_directory
        )
        # WHY: the folder may have been unmounted or deleted since it was chosen (EC-06).
        if not self.show_output_directory_problem_if_any(output_directory):
            return
        download_options_build_result = build_yt_dlp_download_options(
            VideoDownloadRequest(media_url, media_quality_choice, output_directory),
            self.ffmpeg_availability_probe.is_ffmpeg_executable_available(),
        )
        self.last_requested_download_target = (media_url, media_quality_choice)
        self.is_download_active = True
        self.is_download_cancellation_requested = False
        self.download_view.show_download_notice(
            download_options_build_result.ffmpeg_fallback_notice
        )
        self.download_view.show_download_in_progress()
        self.background_worker_pool.submit_background_task(
            lambda: self.media_download_executor.execute_media_download(
                media_url,
                download_options_build_result.yt_dlp_download_options,
                self.forward_download_progress_from_worker_thread,
                lambda: self.is_download_cancellation_requested,
            ),
            self.handle_download_finished,
            self.handle_download_failed,
        )

    def forward_download_progress_from_worker_thread(
        self, download_progress_snapshot: DownloadProgressSnapshot
    ) -> None:
        # WHY: yt-dlp fires hooks many times per second; only the newest snapshot is drawn
        # and at most one render waits in the UI queue at any time.
        self.latest_unrendered_progress_snapshot = download_progress_snapshot
        if self.is_progress_render_scheduled:
            return
        self.is_progress_render_scheduled = True
        self.background_worker_pool.post_callback_to_ui_thread(
            self.render_latest_download_progress_on_ui_thread
        )

    def render_latest_download_progress_on_ui_thread(self) -> None:
        self.is_progress_render_scheduled = False
        latest_progress_snapshot = self.latest_unrendered_progress_snapshot
        if latest_progress_snapshot is None or self.is_download_cancellation_requested:
            return
        self.download_view.show_download_progress(
            build_download_progress_view_model(latest_progress_snapshot)
        )

    def handle_download_finished(self, media_download_outcome: MediaDownloadOutcome) -> None:
        self.is_download_active = False
        downloaded_file_name = (
            os.path.basename(media_download_outcome.downloaded_file_paths[0])
            if media_download_outcome.downloaded_file_paths
            else ""
        )
        completion_prefix = (
            "Já baixado" if media_download_outcome.was_already_downloaded else "Concluído"
        )
        self.download_view.show_download_completed(
            f"{completion_prefix}: {downloaded_file_name}".rstrip(": ")
        )

    def handle_download_failed(self, media_download_error: Exception) -> None:
        self.is_download_active = False
        if isinstance(media_download_error, MediaDownloadCancelledError):
            self.download_view.show_download_cancelled()
            return
        media_download_failure_kind = (
            media_download_error.media_download_failure_kind
            if isinstance(media_download_error, MediaDownloadFailedError)
            else MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE
        )
        self.download_view.show_download_failure(
            describe_media_download_failure_for_user(media_download_failure_kind),
            is_media_download_failure_retryable(media_download_failure_kind),
        )

    def handle_download_requested_for_selection(
        self, download_selection: tuple[str, MediaQualityChoice] | None
    ) -> None:
        if download_selection is None:
            self.download_view.show_download_notice(NO_INSPECTED_MEDIA_TO_DOWNLOAD_NOTICE)
            return
        self.handle_download_requested(*download_selection)

    def handle_download_cancel_requested(self) -> None:
        self.is_download_cancellation_requested = True

    def handle_download_retry_requested(self) -> None:
        if self.last_requested_download_target is None:
            return
        self.handle_download_requested(*self.last_requested_download_target)
