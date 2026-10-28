# WHY: the only module allowed to instantiate adapters and views;
# everything else receives them (ADR-0001).
from videobay_gui import __version__
from videobay_gui.adapters.threading_background_worker_pool_adapter import (
    ThreadingBackgroundWorkerPoolAdapter,
)
from videobay_gui.adapters.urllib_thumbnail_image_fetcher_adapter import (
    UrllibThumbnailImageFetcherAdapter,
)
from videobay_gui.adapters.yt_dlp_metadata_extractor_adapter import YtDlpMetadataExtractorAdapter
from videobay_gui.core.media_inspection_presenter import MediaInspectionPresenter
from videobay_gui.core.videobay_application_identity import build_videobay_main_window_title
from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

UI_CALLBACK_DRAIN_INTERVAL_MILLISECONDS = 100


def build_videobay_gui_application() -> VideobayMainWindowView:
    background_worker_pool = ThreadingBackgroundWorkerPoolAdapter()
    videobay_main_window_view = VideobayMainWindowView(
        build_videobay_main_window_title(__version__)
    )
    media_inspection_panel_view = videobay_main_window_view.media_inspection_panel_view
    media_inspection_presenter = MediaInspectionPresenter(
        media_inspection_panel_view,
        YtDlpMetadataExtractorAdapter(),
        background_worker_pool,
        UrllibThumbnailImageFetcherAdapter(),
    )
    media_inspection_panel_view.bind_media_inspection_presenter_callbacks(
        media_inspection_presenter.handle_media_url_text_changed,
        media_inspection_presenter.handle_inspect_media_url_requested,
    )
    videobay_main_window_view.schedule_recurring_ui_callback(
        UI_CALLBACK_DRAIN_INTERVAL_MILLISECONDS,
        background_worker_pool.drain_completed_callbacks_on_ui_thread,
    )
    # WHY: a pending yt-dlp call must not keep the process alive after the window closes.
    videobay_main_window_view.bind_main_window_close_callback(
        lambda: background_worker_pool.shutdown_background_workers(wait_for_running_tasks=False)
    )
    return videobay_main_window_view


def launch_videobay_gui_application() -> None:
    build_videobay_gui_application().run_videobay_main_event_loop()
