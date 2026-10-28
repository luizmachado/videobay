from tests.unit.video_download_queue_presenter_harness import (
    DEFAULT_DOWNLOAD_DIRECTORY,
    VideoDownloadQueuePresenterTestHarness,
    build_progress_snapshot,
    build_selection,
    queue_harness,
)
from videobay_gui.core.media_download_failure import (
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
    describe_media_download_failure_for_user,
)
from videobay_gui.core.media_download_outcome import MediaDownloadOutcome
from videobay_gui.core.media_quality_choice import (
    MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
)
from videobay_gui.core.video_download_job_row_view_model import VideoDownloadJobRowTone
from videobay_gui.core.video_download_queue_presenter import (
    DUPLICATE_DOWNLOAD_ALREADY_QUEUED_NOTICE,
    NO_INSPECTED_MEDIA_TO_DOWNLOAD_NOTICE,
)
from videobay_gui.core.videobay_user_settings import OutputDirectoryProblem
from videobay_gui.core.yt_dlp_download_options_builder import (
    FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE,
    FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE,
)

__all__ = ["queue_harness"]


def test_download_without_inspected_media_shows_notice(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(None)

    assert queue_harness.queue_view_fake.shown_download_notices == [
        NO_INSPECTED_MEDIA_TO_DOWNLOAD_NOTICE
    ]
    assert queue_harness.queue_view_fake.shown_job_rows == []


def test_ec06_folder_that_disappeared_blocks_adding_to_queue(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.output_directory_probe_fake.output_directory_problems_by_path[
        DEFAULT_DOWNLOAD_DIRECTORY
    ] = OutputDirectoryProblem.OUTPUT_DIRECTORY_MISSING

    queue_harness.request_selection(build_selection())

    assert "não existe" in str(queue_harness.queue_view_fake.shown_download_notices[-1])
    assert queue_harness.queue_view_fake.shown_job_rows == []


def test_ec05_audio_without_ffmpeg_is_blocked_before_queueing(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.ffmpeg_probe_fake.is_ffmpeg_available = False

    queue_harness.request_selection(
        build_selection(media_quality_choice=MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE)
    )

    assert queue_harness.queue_view_fake.shown_download_notices == [
        FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE
    ]
    assert queue_harness.queue_view_fake.shown_job_rows == []


def test_ec04_missing_ffmpeg_for_video_shows_fallback_notice_and_queues(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.ffmpeg_probe_fake.is_ffmpeg_available = False

    queue_harness.request_selection(build_selection())
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    assert queue_harness.queue_view_fake.shown_download_notices == [
        FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE
    ]
    assert queue_harness.download_executor_fake.executed_downloads[0][1]["format"] == "b"


def test_new_job_appears_queued_then_running_with_its_title_and_options(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(
        build_selection(media_quality_choice=MediaQualityChoice(maximum_video_height=720))
    )

    assert queue_harness.queue_view_fake.status_labels_of_job(1) == ["Na fila", "Iniciando…"]
    assert (
        queue_harness.queue_view_fake.latest_row_of_job(1).media_display_title_label == "Vídeo abc"
    )
    queue_harness.worker_pool_fake.drain_pending_background_tasks()
    assert queue_harness.download_executor_fake.executed_downloads[0][1]["format"] == (
        "bv*[height<=720]+ba/b[height<=720]"
    )


def test_concurrency_limit_from_settings_holds_extra_jobs_until_a_slot_frees(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    for video_identifier in ("a", "b", "c"):
        queue_harness.request_selection(build_selection(video_identifier))

    assert queue_harness.queue_view_fake.latest_row_of_job(3).job_status_label == "Na fila"
    queue_harness.worker_pool_fake.drain_pending_background_tasks()
    assert queue_harness.executed_media_urls()[:2] == ["https://youtu.be/a", "https://youtu.be/b"]
    queue_harness.worker_pool_fake.drain_pending_background_tasks()
    assert queue_harness.executed_media_urls() == [
        "https://youtu.be/a",
        "https://youtu.be/b",
        "https://youtu.be/c",
    ]


def test_completed_and_already_downloaded_jobs_show_file_name(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.download_executor_fake.scripted_outcome = MediaDownloadOutcome(
        ("/home/user/Downloads/Aula [abc].mp4",), True
    )

    queue_harness.request_selection(build_selection())
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    completed_row = queue_harness.queue_view_fake.latest_row_of_job(1)
    assert completed_row.job_status_label == "Concluído"
    assert completed_row.job_detail_label == "Já baixado: Aula [abc].mp4"
    assert completed_row.job_row_tone is VideoDownloadJobRowTone.SUCCESS


def test_progress_bursts_are_coalesced_per_job(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.download_executor_fake.scripted_progress_snapshots = [
        build_progress_snapshot(10),
        build_progress_snapshot(20),
        build_progress_snapshot(90),
    ]

    queue_harness.request_selection(build_selection())
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    assert queue_harness.queue_view_fake.status_labels_of_job(1) == [
        "Na fila",
        "Iniciando…",
        "90%",
        "Concluído",
    ]


def test_failed_job_shows_message_and_retry_only_when_retry_can_help(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.download_executor_fake.scripted_download_error = MediaDownloadFailedError(
        MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE, "EACCES"
    )
    queue_harness.request_selection(build_selection("a"))
    queue_harness.worker_pool_fake.drain_pending_background_tasks()
    queue_harness.download_executor_fake.scripted_download_error = RuntimeError("boom")
    queue_harness.request_selection(build_selection("b"))
    queue_harness.worker_pool_fake.drain_pending_background_tasks()

    permission_failure_row = queue_harness.queue_view_fake.latest_row_of_job(1)
    assert permission_failure_row.job_detail_label == describe_media_download_failure_for_user(
        MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE
    )
    assert permission_failure_row.can_retry_video_download_job is False
    assert queue_harness.queue_view_fake.latest_row_of_job(2).can_retry_video_download_job is True


def test_ec10_duplicate_request_shows_notice_and_adds_no_row(
    queue_harness: VideoDownloadQueuePresenterTestHarness,
):
    queue_harness.request_selection(build_selection())
    shown_row_count = len(queue_harness.queue_view_fake.shown_job_rows)

    queue_harness.request_selection(build_selection())

    assert queue_harness.queue_view_fake.shown_download_notices[-1] == (
        DUPLICATE_DOWNLOAD_ALREADY_QUEUED_NOTICE
    )
    assert len(queue_harness.queue_view_fake.shown_job_rows) == shown_row_count
