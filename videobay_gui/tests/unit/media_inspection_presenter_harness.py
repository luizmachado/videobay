"""Shared harness for MediaInspectionPresenter tests (split to respect the 300-line limit)."""

from dataclasses import dataclass

import pytest

from tests.fakes.in_memory_media_metadata_extractor_fake import InMemoryMediaMetadataExtractorFake
from tests.fakes.manually_drained_background_worker_pool_fake import (
    ManuallyDrainedBackgroundWorkerPoolFake,
)
from tests.fakes.recording_media_inspection_view_fake import RecordingMediaInspectionViewFake
from tests.fakes.static_thumbnail_image_fetcher_fake import StaticThumbnailImageFetcherFake
from videobay_gui.core.inspected_media_summary import InspectedMediaSummary
from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailureKind,
    describe_media_inspection_failure_for_user,
)
from videobay_gui.core.media_inspection_presenter import MediaInspectionPresenter

SAMPLE_VIDEO_URL = "https://youtu.be/abc"
SAMPLE_THUMBNAIL_URL = "https://i.ytimg.com/vi/abc/hq.jpg"
SAMPLE_THUMBNAIL_BYTES = b"\xff\xd8fake-jpeg"


@dataclass
class MediaInspectionPresenterTestHarness:
    media_inspection_presenter: MediaInspectionPresenter
    media_inspection_view_fake: RecordingMediaInspectionViewFake
    media_metadata_extractor_fake: InMemoryMediaMetadataExtractorFake
    background_worker_pool_fake: ManuallyDrainedBackgroundWorkerPoolFake
    thumbnail_image_fetcher_fake: StaticThumbnailImageFetcherFake

    def inspect_media_url_and_drain_background(self, raw_media_url: str) -> None:
        self.media_inspection_presenter.handle_inspect_media_url_requested(raw_media_url)
        self.background_worker_pool_fake.drain_pending_background_tasks()

    def last_shown_failure(self) -> tuple[str, bool]:
        return self.media_inspection_view_fake.last_recorded_argument_of(
            "show_media_inspection_failure"
        )


@pytest.fixture
def presenter_harness() -> MediaInspectionPresenterTestHarness:
    media_inspection_view_fake = RecordingMediaInspectionViewFake()
    media_metadata_extractor_fake = InMemoryMediaMetadataExtractorFake()
    background_worker_pool_fake = ManuallyDrainedBackgroundWorkerPoolFake()
    thumbnail_image_fetcher_fake = StaticThumbnailImageFetcherFake()
    return MediaInspectionPresenterTestHarness(
        MediaInspectionPresenter(
            media_inspection_view_fake,
            media_metadata_extractor_fake,
            background_worker_pool_fake,
            thumbnail_image_fetcher_fake,
        ),
        media_inspection_view_fake,
        media_metadata_extractor_fake,
        background_worker_pool_fake,
        thumbnail_image_fetcher_fake,
    )


def build_sample_inspected_media_summary(
    media_url: str = SAMPLE_VIDEO_URL,
    is_live_broadcast: bool = False,
    media_thumbnail_url: str | None = None,
) -> InspectedMediaSummary:
    return InspectedMediaSummary(
        media_url=media_url,
        media_title=f"Título de {media_url}",
        media_uploader_name="Canal",
        media_duration_seconds=60,
        media_thumbnail_url=media_thumbnail_url,
        is_live_broadcast=is_live_broadcast,
    )


def expected_failure_shown_for(
    media_inspection_failure_kind: MediaInspectionFailureKind, can_retry: bool
) -> tuple[str, bool]:
    return (describe_media_inspection_failure_for_user(media_inspection_failure_kind), can_retry)
