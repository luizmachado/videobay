import pytest

from tests.unit.single_media_download_presenter_harness import (
    DOWNLOAD_ATTEMPTS_AFTER_ONE_RETRY,
    SAMPLE_MEDIA_URL,
    SingleMediaDownloadPresenterTestHarness,
    build_progress_snapshot,
    download_harness,
)
from videobay_gui.core.media_download_failure import (
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
    describe_media_download_failure_for_user,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome
from videobay_gui.core.media_quality_choice import (
    BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
)
from videobay_gui.core.single_media_download_presenter import (
    NO_INSPECTED_MEDIA_TO_DOWNLOAD_NOTICE,
)
from videobay_gui.core.yt_dlp_download_options_builder import (
    FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE,
    FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE,
)

__all__ = ["download_harness"]


def test_successful_download_shows_progress_then_completed_filename(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_executor_fake.scripted_progress_snapshots = [
        build_progress_snapshot(30),
        build_progress_snapshot(60),
    ]
    download_harness.download_executor_fake.scripted_outcome = MediaDownloadOutcome(
        ("/home/user/Downloads/Aula [abc].mp4",), False
    )

    download_harness.request_download_and_drain(MediaQualityChoice(maximum_video_height=720))

    view_call_names = download_harness.download_view_fake.recorded_view_call_names()
    assert view_call_names[0] == "show_download_notice"
    assert view_call_names[1] == "show_download_in_progress"
    assert view_call_names[-1] == "show_download_completed"
    assert download_harness.download_view_fake.recorded_arguments_of("show_download_completed") == [
        "Concluído: Aula [abc].mp4"
    ]
    executed_media_url, executed_options = (
        download_harness.download_executor_fake.executed_downloads[0]
    )
    assert executed_media_url == SAMPLE_MEDIA_URL
    assert executed_options["format"] == "bv*[height<=720]+ba/b[height<=720]"


def test_progress_bursts_are_coalesced_to_the_latest_snapshot(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_executor_fake.scripted_progress_snapshots = [
        build_progress_snapshot(10),
        build_progress_snapshot(20),
        build_progress_snapshot(90),
    ]

    download_harness.request_download_and_drain()

    shown_progress = download_harness.download_view_fake.recorded_arguments_of(
        "show_download_progress"
    )
    assert [progress.progress_percentage_label for progress in shown_progress] == ["90%"]


def test_ec04_missing_ffmpeg_shows_fallback_notice_and_still_downloads(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.ffmpeg_probe_fake.is_ffmpeg_available = False

    download_harness.request_download_and_drain()

    assert download_harness.download_view_fake.recorded_arguments_of("show_download_notice")[0] == (
        FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE
    )
    assert download_harness.download_executor_fake.executed_downloads[0][1]["format"] == "b"


def test_ec07_already_downloaded_file_is_reported_as_such(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_executor_fake.scripted_outcome = MediaDownloadOutcome(
        ("/home/user/Downloads/Aula [abc].mp4",), True
    )

    download_harness.request_download_and_drain()

    assert download_harness.download_view_fake.recorded_arguments_of("show_download_completed") == [
        "Já baixado: Aula [abc].mp4"
    ]


@pytest.mark.parametrize(
    ("raised_download_error", "expected_failure_shown"),
    [
        (
            MediaDownloadFailedError(MediaDownloadFailureKind.OUTPUT_DISK_FULL, "ENOSPC"),
            (
                describe_media_download_failure_for_user(MediaDownloadFailureKind.OUTPUT_DISK_FULL),
                True,
            ),
        ),
        (
            RuntimeError("unexpected"),
            (
                describe_media_download_failure_for_user(
                    MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE
                ),
                True,
            ),
        ),
    ],
)
def test_download_failures_become_messages_with_retry_rule(
    download_harness: SingleMediaDownloadPresenterTestHarness,
    raised_download_error: Exception,
    expected_failure_shown: tuple[str, bool],
):
    download_harness.download_executor_fake.scripted_download_error = raised_download_error

    download_harness.request_download_and_drain()

    assert download_harness.download_view_fake.recorded_arguments_of("show_download_failure") == [
        expected_failure_shown
    ]


def test_ec09_cancel_stops_download_and_progress_after_cancel_is_not_drawn(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_executor_fake.scripted_progress_snapshots = [
        build_progress_snapshot(10),
        build_progress_snapshot(20),
    ]
    download_harness.download_presenter.handle_download_requested(
        SAMPLE_MEDIA_URL, BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
    )

    download_harness.download_presenter.handle_download_cancel_requested()
    download_harness.worker_pool_fake.drain_pending_background_tasks()

    view_call_names = download_harness.download_view_fake.recorded_view_call_names()
    assert view_call_names[-1] == "show_download_cancelled"
    assert "show_download_progress" not in view_call_names


def test_second_request_while_downloading_is_ignored(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_presenter.handle_download_requested(
        SAMPLE_MEDIA_URL, BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
    )
    download_harness.download_presenter.handle_download_requested(
        SAMPLE_MEDIA_URL, BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
    )

    assert len(download_harness.worker_pool_fake.pending_background_tasks) == 1


def test_retry_repeats_the_last_download_after_failure(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_executor_fake.scripted_download_error = MediaDownloadFailedError(
        MediaDownloadFailureKind.NETWORK_UNREACHABLE, "reset"
    )
    download_harness.request_download_and_drain(MediaQualityChoice(maximum_video_height=480))
    download_harness.download_executor_fake.scripted_download_error = None

    download_harness.download_presenter.handle_download_retry_requested()
    download_harness.worker_pool_fake.drain_pending_background_tasks()

    executed_downloads = download_harness.download_executor_fake.executed_downloads
    assert len(executed_downloads) == DOWNLOAD_ATTEMPTS_AFTER_ONE_RETRY
    assert executed_downloads[1][1]["format"] == executed_downloads[0][1]["format"]
    assert download_harness.download_view_fake.recorded_view_call_names()[-1] == (
        "show_download_completed"
    )


def test_retry_without_previous_download_does_nothing(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_presenter.handle_download_retry_requested()

    assert download_harness.worker_pool_fake.pending_background_tasks == []


def test_ec09_progress_posted_before_cancel_is_dropped_when_ui_drains_after_cancel(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_presenter = download_harness.download_presenter
    download_presenter.forward_download_progress_from_worker_thread(build_progress_snapshot(40))

    download_presenter.handle_download_cancel_requested()
    download_harness.worker_pool_fake.drain_pending_background_tasks()

    assert "show_download_progress" not in (
        download_harness.download_view_fake.recorded_view_call_names()
    )


def test_download_without_inspected_media_shows_notice_instead_of_starting(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_presenter.handle_download_requested_for_selection(None)

    assert download_harness.worker_pool_fake.pending_background_tasks == []
    assert download_harness.download_view_fake.recorded_arguments_of("show_download_notice") == [
        NO_INSPECTED_MEDIA_TO_DOWNLOAD_NOTICE
    ]


def test_download_for_selection_starts_download_of_selected_target(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.download_presenter.handle_download_requested_for_selection(
        (SAMPLE_MEDIA_URL, BEST_AVAILABLE_MEDIA_QUALITY_CHOICE)
    )

    assert len(download_harness.worker_pool_fake.pending_background_tasks) == 1


def test_ec05_audio_download_without_ffmpeg_is_blocked_before_starting(
    download_harness: SingleMediaDownloadPresenterTestHarness,
):
    download_harness.ffmpeg_probe_fake.is_ffmpeg_available = False

    download_harness.request_download_and_drain(MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE)

    assert download_harness.download_executor_fake.executed_downloads == []
    assert "show_download_in_progress" not in (
        download_harness.download_view_fake.recorded_view_call_names()
    )
    assert download_harness.download_view_fake.recorded_arguments_of("show_download_notice") == [
        FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE
    ]
