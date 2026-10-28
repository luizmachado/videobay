"""Shared harness for VideoDownloadQueuePresenter tests (split to respect the 300-line limit)."""

from dataclasses import dataclass

import pytest

from tests.fakes.in_memory_videobay_settings_store_fake import InMemoryVideobaySettingsStoreFake
from tests.fakes.manually_drained_background_worker_pool_fake import (
    ManuallyDrainedBackgroundWorkerPoolFake,
)
from tests.fakes.recording_video_download_queue_view_fake import (
    RecordingVideoDownloadQueueViewFake,
)
from tests.fakes.scripted_download_environment_probes_fake import (
    FixedFfmpegAvailabilityProbeFake,
    ScriptedOutputDirectoryAccessProbeFake,
)
from tests.fakes.scripted_media_download_executor_fake import ScriptedMediaDownloadExecutorFake
from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_download_selection import MediaDownloadSelection
from videobay_gui.core.media_quality_choice import (
    BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
)
from videobay_gui.core.video_download_queue_presenter import (
    VideoDownloadQueuePorts,
    VideoDownloadQueuePresenter,
)

DEFAULT_DOWNLOAD_DIRECTORY = "/home/user/Downloads"


def build_selection(
    video_identifier: str = "abc",
    media_quality_choice: MediaQualityChoice = BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
) -> MediaDownloadSelection:
    return MediaDownloadSelection(
        f"https://youtu.be/{video_identifier}", media_quality_choice, f"Vídeo {video_identifier}"
    )


def build_progress_snapshot(downloaded_byte_count: int) -> DownloadProgressSnapshot:
    return DownloadProgressSnapshot(downloaded_byte_count, 100, False, None, None)


@dataclass
class VideoDownloadQueuePresenterTestHarness:
    queue_presenter: VideoDownloadQueuePresenter
    queue_view_fake: RecordingVideoDownloadQueueViewFake
    download_executor_fake: ScriptedMediaDownloadExecutorFake
    worker_pool_fake: ManuallyDrainedBackgroundWorkerPoolFake
    settings_store_fake: InMemoryVideobaySettingsStoreFake
    output_directory_probe_fake: ScriptedOutputDirectoryAccessProbeFake
    ffmpeg_probe_fake: FixedFfmpegAvailabilityProbeFake

    def request_selection(self, media_download_selection: MediaDownloadSelection | None) -> None:
        self.queue_presenter.handle_download_requested_for_selection(media_download_selection)

    def executed_media_urls(self) -> list[str]:
        return [media_url for media_url, _ in self.download_executor_fake.executed_downloads]


@pytest.fixture
def queue_harness() -> VideoDownloadQueuePresenterTestHarness:
    queue_view_fake = RecordingVideoDownloadQueueViewFake()
    download_executor_fake = ScriptedMediaDownloadExecutorFake()
    worker_pool_fake = ManuallyDrainedBackgroundWorkerPoolFake()
    settings_store_fake = InMemoryVideobaySettingsStoreFake(DEFAULT_DOWNLOAD_DIRECTORY)
    output_directory_probe_fake = ScriptedOutputDirectoryAccessProbeFake()
    ffmpeg_probe_fake = FixedFfmpegAvailabilityProbeFake(is_ffmpeg_available=True)
    queue_presenter = VideoDownloadQueuePresenter(
        queue_view_fake,
        VideoDownloadQueuePorts(
            download_executor_fake,
            worker_pool_fake,
            settings_store_fake,
            output_directory_probe_fake,
            ffmpeg_probe_fake,
        ),
    )
    return VideoDownloadQueuePresenterTestHarness(
        queue_presenter,
        queue_view_fake,
        download_executor_fake,
        worker_pool_fake,
        settings_store_fake,
        output_directory_probe_fake,
        ffmpeg_probe_fake,
    )
