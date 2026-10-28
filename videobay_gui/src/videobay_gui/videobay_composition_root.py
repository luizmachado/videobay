# WHY: the only module allowed to instantiate adapters and views;
# everything else receives them (ADR-0001).
import os
import shutil
import sys
from pathlib import Path

from videobay_gui import __version__
from videobay_gui.adapters.bundled_deno_runtime_locator import locate_deno_executable_for_yt_dlp
from videobay_gui.adapters.json_file_videobay_settings_store_adapter import (
    JsonFileVideobaySettingsStoreAdapter,
)
from videobay_gui.adapters.local_output_directory_access_probe_adapter import (
    LocalOutputDirectoryAccessProbeAdapter,
    resolve_default_videobay_output_directory,
)
from videobay_gui.adapters.shutil_which_ffmpeg_probe_adapter import ShutilWhichFfmpegProbeAdapter
from videobay_gui.adapters.threading_background_worker_pool_adapter import (
    ThreadingBackgroundWorkerPoolAdapter,
)
from videobay_gui.adapters.urllib_thumbnail_image_fetcher_adapter import (
    UrllibThumbnailImageFetcherAdapter,
)
from videobay_gui.adapters.yt_dlp_download_executor_adapter import YtDlpDownloadExecutorAdapter
from videobay_gui.adapters.yt_dlp_metadata_extractor_adapter import YtDlpMetadataExtractorAdapter
from videobay_gui.core.media_inspection_presenter import MediaInspectionPresenter
from videobay_gui.core.video_download_queue_presenter import (
    VideoDownloadQueuePorts,
    VideoDownloadQueuePresenter,
)
from videobay_gui.core.videobay_application_identity import build_videobay_main_window_title
from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

UI_CALLBACK_DRAIN_INTERVAL_MILLISECONDS = 100


def build_videobay_settings_file_path() -> Path:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(xdg_config_home) / "videobay" / "settings.json"


def build_videobay_gui_application() -> VideobayMainWindowView:
    background_worker_pool = ThreadingBackgroundWorkerPoolAdapter()
    # PROVENANCE: ADR-0008. sys._MEIPASS only exists inside the PyInstaller binary.
    deno_executable_path = locate_deno_executable_for_yt_dlp(
        getattr(sys, "_MEIPASS", None), shutil.which
    )
    videobay_main_window_view = VideobayMainWindowView(
        build_videobay_main_window_title(__version__)
    )
    media_inspection_panel_view = videobay_main_window_view.media_inspection_panel_view
    media_inspection_presenter = MediaInspectionPresenter(
        media_inspection_panel_view,
        YtDlpMetadataExtractorAdapter(deno_executable_path=deno_executable_path),
        background_worker_pool,
        UrllibThumbnailImageFetcherAdapter(),
    )
    media_inspection_panel_view.bind_media_inspection_presenter_callbacks(
        media_inspection_presenter.handle_media_url_text_changed,
        media_inspection_presenter.handle_inspect_media_url_requested,
        media_inspection_presenter.handle_media_quality_choice_selected,
    )
    video_download_queue_panel_view = videobay_main_window_view.video_download_queue_panel_view
    video_download_queue_presenter = VideoDownloadQueuePresenter(
        video_download_queue_panel_view,
        VideoDownloadQueuePorts(
            YtDlpDownloadExecutorAdapter(deno_executable_path=deno_executable_path),
            background_worker_pool,
            JsonFileVideobaySettingsStoreAdapter(
                build_videobay_settings_file_path(),
                resolve_default_videobay_output_directory(os.path.expanduser("~")),
            ),
            LocalOutputDirectoryAccessProbeAdapter(),
            ShutilWhichFfmpegProbeAdapter(shutil.which),
        ),
    )
    video_download_queue_panel_view.bind_video_download_queue_presenter_callbacks(
        video_download_queue_presenter.handle_output_directory_chosen,
        lambda: video_download_queue_presenter.handle_download_requested_for_selection(
            media_inspection_presenter.current_download_selection()
        ),
        video_download_queue_presenter.handle_video_download_job_cancel_requested,
        video_download_queue_presenter.handle_video_download_job_retry_requested,
    )
    video_download_queue_presenter.present_initial_download_state()
    videobay_main_window_view.schedule_recurring_ui_callback(
        UI_CALLBACK_DRAIN_INTERVAL_MILLISECONDS,
        background_worker_pool.drain_completed_callbacks_on_ui_thread,
    )
    # WHY: a pending yt-dlp call must not keep the process alive after the window closes.
    videobay_main_window_view.bind_main_window_close_callback(
        video_download_queue_presenter.handle_main_window_close_requested,
        lambda: background_worker_pool.shutdown_background_workers(wait_for_running_tasks=False),
    )
    return videobay_main_window_view


def launch_videobay_gui_application() -> None:
    build_videobay_gui_application().run_videobay_main_event_loop()
