# pyright: basic
# WHY: drives real CustomTkinter widgets (untyped) wired to the real presenter and test fakes.
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from tests.fakes.in_memory_videobay_settings_store_fake import InMemoryVideobaySettingsStoreFake
from tests.fakes.manually_drained_background_worker_pool_fake import (
    ManuallyDrainedBackgroundWorkerPoolFake,
)
from tests.fakes.scripted_download_environment_probes_fake import (
    FixedFfmpegAvailabilityProbeFake,
    ScriptedOutputDirectoryAccessProbeFake,
)
from tests.fakes.scripted_media_download_executor_fake import ScriptedMediaDownloadExecutorFake
from videobay_gui.core.media_download_failure import (
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
)
from videobay_gui.core.media_download_selection import MediaDownloadSelection
from videobay_gui.core.media_quality_choice import BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
from videobay_gui.core.video_download_queue_presenter import (
    VideoDownloadQueuePorts,
    VideoDownloadQueuePresenter,
)

if TYPE_CHECKING:
    from videobay_gui.views.video_download_queue_panel_view import VideoDownloadQueuePanelView
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

pytestmark = pytest.mark.ui

SMOKE_DOWNLOAD_DIRECTORY = "/home/smoke/Downloads"


@dataclass
class VideoDownloadQueuePanelSmokeRig:
    main_window_view: "VideobayMainWindowView"
    panel_view: "VideoDownloadQueuePanelView"
    executor_fake: ScriptedMediaDownloadExecutorFake
    worker_pool_fake: ManuallyDrainedBackgroundWorkerPoolFake
    next_video_identifiers: list[str]

    def click_download(self) -> None:
        self.panel_view.start_download_button.invoke()
        self.main_window_view.update()

    def finish_background(self) -> None:
        self.worker_pool_fake.drain_pending_background_tasks()
        self.main_window_view.update()

    def row_status_text(self, job_identifier: int) -> str:
        return self.panel_view.job_row_widgets_by_identifier[job_identifier].status_label.cget(
            "text"
        )


@pytest.fixture
def smoke_rig() -> Iterator[VideoDownloadQueuePanelSmokeRig]:
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

    main_window_view = VideobayMainWindowView("VideoBay smoke")
    panel_view = main_window_view.video_download_queue_panel_view
    smoke_rig = VideoDownloadQueuePanelSmokeRig(
        main_window_view,
        panel_view,
        ScriptedMediaDownloadExecutorFake(),
        ManuallyDrainedBackgroundWorkerPoolFake(),
        ["a", "b", "c"],
    )
    queue_presenter = VideoDownloadQueuePresenter(
        panel_view,
        VideoDownloadQueuePorts(
            smoke_rig.executor_fake,
            smoke_rig.worker_pool_fake,
            InMemoryVideobaySettingsStoreFake(SMOKE_DOWNLOAD_DIRECTORY),
            ScriptedOutputDirectoryAccessProbeFake(),
            FixedFfmpegAvailabilityProbeFake(is_ffmpeg_available=True),
        ),
    )
    panel_view.bind_video_download_queue_presenter_callbacks(
        queue_presenter.handle_output_directory_chosen,
        lambda: queue_presenter.handle_download_requested_for_selection(
            MediaDownloadSelection(
                f"https://youtu.be/{smoke_rig.next_video_identifiers.pop(0)}",
                BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
                "Vídeo de teste",
            )
        ),
        queue_presenter.handle_video_download_job_cancel_requested,
        queue_presenter.handle_video_download_job_retry_requested,
    )
    queue_presenter.present_initial_download_state()
    main_window_view.update()
    yield smoke_rig
    main_window_view.destroy()


def test_three_downloads_show_two_running_one_queued_then_all_complete(
    smoke_rig: VideoDownloadQueuePanelSmokeRig,
):
    for _ in range(3):
        smoke_rig.click_download()

    assert [smoke_rig.row_status_text(job_identifier) for job_identifier in (1, 2, 3)] == [
        "Iniciando…",
        "Iniciando…",
        "Na fila",
    ]
    assert smoke_rig.panel_view.job_row_widgets_by_identifier[3].cancel_button.winfo_ismapped()

    smoke_rig.finish_background()
    smoke_rig.finish_background()

    assert [smoke_rig.row_status_text(job_identifier) for job_identifier in (1, 2, 3)] == [
        "Concluído"
    ] * 3
    assert not smoke_rig.panel_view.job_row_widgets_by_identifier[1].cancel_button.winfo_ismapped()


def test_row_cancel_button_cancels_that_job_only(smoke_rig: VideoDownloadQueuePanelSmokeRig):
    smoke_rig.click_download()
    smoke_rig.click_download()

    smoke_rig.panel_view.job_row_widgets_by_identifier[2].cancel_button.invoke()
    smoke_rig.finish_background()

    assert smoke_rig.row_status_text(1) == "Concluído"
    assert smoke_rig.row_status_text(2) == "Cancelado"
    assert smoke_rig.panel_view.job_row_widgets_by_identifier[2].retry_button.winfo_ismapped()


def test_retryable_failure_shows_message_and_retry_runs_again(
    smoke_rig: VideoDownloadQueuePanelSmokeRig,
):
    smoke_rig.executor_fake.scripted_download_error = MediaDownloadFailedError(
        MediaDownloadFailureKind.NETWORK_UNREACHABLE, "reset"
    )
    smoke_rig.click_download()
    smoke_rig.finish_background()
    job_row = smoke_rig.panel_view.job_row_widgets_by_identifier[1]
    assert smoke_rig.row_status_text(1) == "Falhou"
    assert "conexão caiu" in job_row.detail_label.cget("text")

    smoke_rig.executor_fake.scripted_download_error = None
    job_row.retry_button.invoke()
    smoke_rig.finish_background()

    assert smoke_rig.row_status_text(1) == "Concluído"
