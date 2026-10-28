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
from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_download_failure import (
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome
from videobay_gui.core.media_quality_choice import BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
from videobay_gui.core.single_media_download_presenter import (
    SingleMediaDownloadPorts,
    SingleMediaDownloadPresenter,
)

if TYPE_CHECKING:
    from videobay_gui.views.single_media_download_panel_view import SingleMediaDownloadPanelView
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

pytestmark = pytest.mark.ui

SMOKE_DOWNLOAD_DIRECTORY = "/home/smoke/Downloads"
SMOKE_DOWNLOAD_SELECTION = ("https://youtu.be/abc", BEST_AVAILABLE_MEDIA_QUALITY_CHOICE)


@dataclass
class SingleMediaDownloadPanelSmokeRig:
    main_window_view: "VideobayMainWindowView"
    panel_view: "SingleMediaDownloadPanelView"
    executor_fake: ScriptedMediaDownloadExecutorFake
    worker_pool_fake: ManuallyDrainedBackgroundWorkerPoolFake
    ffmpeg_probe_fake: FixedFfmpegAvailabilityProbeFake

    def click_download_and_finish_background(self) -> None:
        self.panel_view.start_download_button.invoke()
        self.main_window_view.update()
        self.worker_pool_fake.drain_pending_background_tasks()
        self.main_window_view.update()


@pytest.fixture
def smoke_rig() -> Iterator[SingleMediaDownloadPanelSmokeRig]:
    from videobay_gui.views.videobay_main_window_view import VideobayMainWindowView

    main_window_view = VideobayMainWindowView("VideoBay smoke")
    panel_view = main_window_view.single_media_download_panel_view
    smoke_rig = SingleMediaDownloadPanelSmokeRig(
        main_window_view,
        panel_view,
        ScriptedMediaDownloadExecutorFake(),
        ManuallyDrainedBackgroundWorkerPoolFake(),
        FixedFfmpegAvailabilityProbeFake(is_ffmpeg_available=True),
    )
    download_presenter = SingleMediaDownloadPresenter(
        panel_view,
        SingleMediaDownloadPorts(
            smoke_rig.executor_fake,
            smoke_rig.worker_pool_fake,
            InMemoryVideobaySettingsStoreFake(SMOKE_DOWNLOAD_DIRECTORY),
            ScriptedOutputDirectoryAccessProbeFake(),
            smoke_rig.ffmpeg_probe_fake,
        ),
    )
    panel_view.bind_single_media_download_presenter_callbacks(
        download_presenter.handle_output_directory_chosen,
        lambda: download_presenter.handle_download_requested_for_selection(
            SMOKE_DOWNLOAD_SELECTION
        ),
        download_presenter.handle_download_cancel_requested,
        download_presenter.handle_download_retry_requested,
    )
    download_presenter.present_initial_download_state()
    main_window_view.update()
    yield smoke_rig
    main_window_view.destroy()


def test_shows_saved_folder_and_completes_download_with_progress(
    smoke_rig: SingleMediaDownloadPanelSmokeRig,
):
    smoke_rig.executor_fake.scripted_progress_snapshots = [
        DownloadProgressSnapshot(50, 100, False, 2048.0, 3)
    ]
    smoke_rig.executor_fake.scripted_outcome = MediaDownloadOutcome(
        (f"{SMOKE_DOWNLOAD_DIRECTORY}/Aula [abc].mp4",), False
    )

    assert smoke_rig.panel_view.output_directory_label.cget("text") == SMOKE_DOWNLOAD_DIRECTORY
    smoke_rig.click_download_and_finish_background()

    assert smoke_rig.panel_view.download_status_label.cget("text") == "Concluído: Aula [abc].mp4"
    assert smoke_rig.panel_view.download_progress_bar.get() == pytest.approx(1.0)
    assert smoke_rig.panel_view.start_download_button.cget("state") == "normal"
    assert not smoke_rig.panel_view.cancel_download_button.winfo_ismapped()


def test_ec04_missing_ffmpeg_notice_is_visible(smoke_rig: SingleMediaDownloadPanelSmokeRig):
    smoke_rig.ffmpeg_probe_fake.is_ffmpeg_available = False

    smoke_rig.click_download_and_finish_background()

    assert "ffmpeg" in smoke_rig.panel_view.download_notice_label.cget("text")


def test_in_progress_state_shows_cancel_and_disables_download(
    smoke_rig: SingleMediaDownloadPanelSmokeRig,
):
    smoke_rig.panel_view.start_download_button.invoke()
    smoke_rig.main_window_view.update()

    assert smoke_rig.panel_view.start_download_button.cget("state") == "disabled"
    assert smoke_rig.panel_view.cancel_download_button.winfo_ismapped()

    smoke_rig.panel_view.cancel_download_button.invoke()
    smoke_rig.worker_pool_fake.drain_pending_background_tasks()
    smoke_rig.main_window_view.update()

    assert smoke_rig.panel_view.download_status_label.cget("text") == "Download cancelado."


def test_retryable_failure_shows_retry_button(smoke_rig: SingleMediaDownloadPanelSmokeRig):
    smoke_rig.executor_fake.scripted_download_error = MediaDownloadFailedError(
        MediaDownloadFailureKind.NETWORK_UNREACHABLE, "reset"
    )

    smoke_rig.click_download_and_finish_background()

    assert "conexão caiu" in smoke_rig.panel_view.download_status_label.cget("text")
    assert smoke_rig.panel_view.retry_download_button.winfo_ismapped()
