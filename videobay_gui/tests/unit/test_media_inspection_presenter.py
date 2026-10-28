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
    MediaInspectionFailedError,
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


@pytest.mark.parametrize(
    ("raw_media_url", "expected_message_mentions_http", "expected_action_enabled"),
    [
        ("youtube.com/x", True, False),
        ("   ", False, False),
        (SAMPLE_VIDEO_URL, False, True),
    ],
)
def test_ec01_url_text_changes_drive_validation_message_and_inspect_action(
    presenter_harness: MediaInspectionPresenterTestHarness,
    raw_media_url: str,
    expected_message_mentions_http: bool,
    expected_action_enabled: bool,
):
    presenter_harness.media_inspection_presenter.handle_media_url_text_changed(raw_media_url)

    view_fake = presenter_harness.media_inspection_view_fake
    shown_validation_message = view_fake.last_recorded_argument_of(
        "show_media_url_validation_message"
    )
    assert (shown_validation_message is not None) is expected_message_mentions_http
    if expected_message_mentions_http:
        assert "http" in shown_validation_message
    assert view_fake.last_recorded_argument_of("set_inspect_media_url_action_enabled") is (
        expected_action_enabled
    )


def test_inspection_request_with_invalid_url_never_reaches_extractor(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    presenter_harness.media_inspection_presenter.handle_inspect_media_url_requested("ftp://x.com/v")

    assert presenter_harness.background_worker_pool_fake.pending_background_tasks == []
    assert (
        presenter_harness.media_inspection_view_fake.last_recorded_argument_of(
            "set_inspect_media_url_action_enabled"
        )
        is False
    )


def test_successful_inspection_runs_in_background_then_shows_summary(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        build_sample_inspected_media_summary()
    )

    presenter_harness.media_inspection_presenter.handle_inspect_media_url_requested(
        f"  {SAMPLE_VIDEO_URL} "
    )
    assert presenter_harness.media_inspection_view_fake.recorded_view_call_names()[-1] == (
        "show_media_inspection_in_progress"
    )
    assert presenter_harness.media_metadata_extractor_fake.extracted_media_urls == []

    presenter_harness.background_worker_pool_fake.drain_pending_background_tasks()

    assert presenter_harness.media_metadata_extractor_fake.extracted_media_urls == [
        SAMPLE_VIDEO_URL
    ]
    shown_view_model = presenter_harness.media_inspection_view_fake.last_recorded_argument_of(
        "show_inspected_media_summary"
    )
    assert shown_view_model.media_title_label == f"Título de {SAMPLE_VIDEO_URL}"
    assert presenter_harness.media_inspection_presenter.latest_inspected_media_summary is not None


@pytest.mark.parametrize(
    ("media_inspection_failure_kind", "expected_can_retry"),
    [
        (MediaInspectionFailureKind.UNSUPPORTED_SITE, False),
        (MediaInspectionFailureKind.MEDIA_UNAVAILABLE, False),
        (MediaInspectionFailureKind.NETWORK_UNREACHABLE, True),
    ],
)
def test_ec02_ec03_extractor_failures_become_user_messages(
    presenter_harness: MediaInspectionPresenterTestHarness,
    media_inspection_failure_kind: MediaInspectionFailureKind,
    expected_can_retry: bool,
):
    presenter_harness.media_metadata_extractor_fake.script_extraction_error(
        SAMPLE_VIDEO_URL, MediaInspectionFailedError(media_inspection_failure_kind, "detail")
    )

    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)

    assert presenter_harness.last_shown_failure() == expected_failure_shown_for(
        media_inspection_failure_kind, expected_can_retry
    )
    assert presenter_harness.media_inspection_presenter.latest_inspected_media_summary is None


def test_unexpected_exception_is_reported_as_retryable_unknown_failure(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    presenter_harness.media_metadata_extractor_fake.script_extraction_error(
        SAMPLE_VIDEO_URL, KeyError("formats")
    )

    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)

    assert presenter_harness.last_shown_failure() == expected_failure_shown_for(
        MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE, True
    )


def test_ec17_live_broadcast_is_rejected_after_inspection(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        build_sample_inspected_media_summary(is_live_broadcast=True)
    )

    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)

    assert "show_inspected_media_summary" not in (
        presenter_harness.media_inspection_view_fake.recorded_view_call_names()
    )
    assert presenter_harness.last_shown_failure() == expected_failure_shown_for(
        MediaInspectionFailureKind.LIVE_BROADCAST_NOT_SUPPORTED, False
    )


@pytest.mark.parametrize("stale_result_is_failure", [False, True])
def test_stale_result_from_previous_url_is_discarded(
    presenter_harness: MediaInspectionPresenterTestHarness, stale_result_is_failure: bool
):
    newer_video_url = "https://youtu.be/newer"
    extractor_fake = presenter_harness.media_metadata_extractor_fake
    if stale_result_is_failure:
        extractor_fake.script_extraction_error(SAMPLE_VIDEO_URL, KeyError("stale"))
    else:
        extractor_fake.script_media_summary(build_sample_inspected_media_summary())
    extractor_fake.script_media_summary(build_sample_inspected_media_summary(newer_video_url))

    presenter_harness.media_inspection_presenter.handle_inspect_media_url_requested(
        SAMPLE_VIDEO_URL
    )
    presenter_harness.inspect_media_url_and_drain_background(newer_video_url)

    view_call_names = presenter_harness.media_inspection_view_fake.recorded_view_call_names()
    assert "show_media_inspection_failure" not in view_call_names
    assert view_call_names.count("show_inspected_media_summary") == 1
    shown_view_model = presenter_harness.media_inspection_view_fake.last_recorded_argument_of(
        "show_inspected_media_summary"
    )
    assert shown_view_model.media_title_label == f"Título de {newer_video_url}"


def test_thumbnail_is_fetched_in_background_after_summary_is_shown(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        build_sample_inspected_media_summary(media_thumbnail_url=SAMPLE_THUMBNAIL_URL)
    )
    presenter_harness.thumbnail_image_fetcher_fake.script_thumbnail_image_bytes(
        SAMPLE_THUMBNAIL_URL, SAMPLE_THUMBNAIL_BYTES
    )

    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)
    assert presenter_harness.thumbnail_image_fetcher_fake.fetched_thumbnail_urls == []
    presenter_harness.background_worker_pool_fake.drain_pending_background_tasks()

    assert presenter_harness.media_inspection_view_fake.recorded_view_call_names()[-2:] == [
        "show_inspected_media_summary",
        "show_media_thumbnail_image",
    ]
    assert (
        presenter_harness.media_inspection_view_fake.last_recorded_argument_of(
            "show_media_thumbnail_image"
        )
        == SAMPLE_THUMBNAIL_BYTES
    )


@pytest.mark.parametrize("media_thumbnail_url", [None, "https://i.ytimg.com/broken.jpg"])
def test_ec14_missing_or_failed_thumbnail_shows_placeholder_without_error(
    presenter_harness: MediaInspectionPresenterTestHarness, media_thumbnail_url: str | None
):
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        build_sample_inspected_media_summary(media_thumbnail_url=media_thumbnail_url)
    )

    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)
    presenter_harness.background_worker_pool_fake.drain_pending_background_tasks()

    view_call_names = presenter_harness.media_inspection_view_fake.recorded_view_call_names()
    assert view_call_names[-1] == "show_media_thumbnail_placeholder"
    assert "show_media_inspection_failure" not in view_call_names


@pytest.mark.parametrize("stale_thumbnail_fetch_fails", [False, True])
def test_stale_thumbnail_from_previous_url_is_discarded(
    presenter_harness: MediaInspectionPresenterTestHarness, stale_thumbnail_fetch_fails: bool
):
    newer_video_url = "https://youtu.be/newer"
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        build_sample_inspected_media_summary(media_thumbnail_url=SAMPLE_THUMBNAIL_URL)
    )
    if not stale_thumbnail_fetch_fails:
        presenter_harness.thumbnail_image_fetcher_fake.script_thumbnail_image_bytes(
            SAMPLE_THUMBNAIL_URL, SAMPLE_THUMBNAIL_BYTES
        )
    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)

    presenter_harness.media_inspection_presenter.handle_inspect_media_url_requested(newer_video_url)
    presenter_harness.background_worker_pool_fake.pending_background_tasks.reverse()
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        build_sample_inspected_media_summary(newer_video_url)
    )
    presenter_harness.background_worker_pool_fake.drain_pending_background_tasks()

    view_call_names = presenter_harness.media_inspection_view_fake.recorded_view_call_names()
    assert "show_media_thumbnail_image" not in view_call_names
    assert view_call_names[-1] == "show_media_thumbnail_placeholder"
