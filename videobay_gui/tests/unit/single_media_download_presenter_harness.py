"""Shared harness for SingleMediaDownloadPresenter tests (split to respect the 300-line limit)."""

from dataclasses import dataclass

import pytest

from tests.fakes.in_memory_videobay_settings_store_fake import InMemoryVideobaySettingsStoreFake
from tests.fakes.manually_drained_background_worker_pool_fake import (
    ManuallyDrainedBackgroundWorkerPoolFake,
)
from tests.fakes.recording_single_media_download_view_fake import (
    RecordingSingleMediaDownloadViewFake,
)
from tests.fakes.scripted_download_environment_probes_fake import (
    FixedFfmpegAvailabilityProbeFake,
    ScriptedOutputDirectoryAccessProbeFake,
)
from tests.fakes.scripted_media_download_executor_fake import ScriptedMediaDownloadExecutorFake
from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_quality_choice import (
    BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
)
from videobay_gui.core.single_media_download_presenter import (
    SingleMediaDownloadPorts,
    SingleMediaDownloadPresenter,
)

DEFAULT_DOWNLOAD_DIRECTORY = "/home/user/Downloads"
SAMPLE_MEDIA_URL = "https://youtu.be/abc"
DOWNLOAD_ATTEMPTS_AFTER_ONE_RETRY = 2


def build_progress_snapshot(downloaded_byte_count: int) -> DownloadProgressSnapshot:
    return DownloadProgressSnapshot(downloaded_byte_count, 100, False, None, None)


@dataclass
class SingleMediaDownloadPresenterTestHarness:
    download_presenter: SingleMediaDownloadPresenter
    download_view_fake: RecordingSingleMediaDownloadViewFake
    download_executor_fake: ScriptedMediaDownloadExecutorFake
    worker_pool_fake: ManuallyDrainedBackgroundWorkerPoolFake
    settings_store_fake: InMemoryVideobaySettingsStoreFake
    output_directory_probe_fake: ScriptedOutputDirectoryAccessProbeFake
    ffmpeg_probe_fake: FixedFfmpegAvailabilityProbeFake

    def request_download_and_drain(
        self, media_quality_choice: MediaQualityChoice = BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
    ) -> None:
        self.download_presenter.handle_download_requested(SAMPLE_MEDIA_URL, media_quality_choice)
        self.worker_pool_fake.drain_pending_background_tasks()


@pytest.fixture
def download_harness() -> SingleMediaDownloadPresenterTestHarness:
    download_view_fake = RecordingSingleMediaDownloadViewFake()
    download_executor_fake = ScriptedMediaDownloadExecutorFake()
    worker_pool_fake = ManuallyDrainedBackgroundWorkerPoolFake()
    settings_store_fake = InMemoryVideobaySettingsStoreFake(DEFAULT_DOWNLOAD_DIRECTORY)
    output_directory_probe_fake = ScriptedOutputDirectoryAccessProbeFake()
    ffmpeg_probe_fake = FixedFfmpegAvailabilityProbeFake(is_ffmpeg_available=True)
    download_presenter = SingleMediaDownloadPresenter(
        download_view_fake,
        SingleMediaDownloadPorts(
            download_executor_fake,
            worker_pool_fake,
            settings_store_fake,
            output_directory_probe_fake,
            ffmpeg_probe_fake,
        ),
    )
    return SingleMediaDownloadPresenterTestHarness(
        download_presenter,
        download_view_fake,
        download_executor_fake,
        worker_pool_fake,
        settings_store_fake,
        output_directory_probe_fake,
        ffmpeg_probe_fake,
    )
