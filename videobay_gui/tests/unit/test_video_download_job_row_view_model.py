import pytest

from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_quality_choice import BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
from videobay_gui.core.video_download_job import VideoDownloadJob, VideoDownloadJobStatus
from videobay_gui.core.video_download_job_row_view_model import (
    VideoDownloadJobRowTone,
    build_video_download_job_row_view_model,
)
from videobay_gui.core.video_download_request import VideoDownloadRequest

SAMPLE_JOB_IDENTIFIER = 4


def build_job(
    video_download_job_status: VideoDownloadJobStatus, media_display_title: str = "Aula de Python"
) -> VideoDownloadJob:
    return VideoDownloadJob(
        SAMPLE_JOB_IDENTIFIER,
        VideoDownloadRequest("https://youtu.be/abc", BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, "/d"),
        video_download_job_status,
        media_display_title,
    )


@pytest.mark.parametrize(
    ("video_download_job_status", "expected_status_label", "can_cancel", "can_retry", "tone"),
    [
        (VideoDownloadJobStatus.QUEUED, "Na fila", True, False, VideoDownloadJobRowTone.NEUTRAL),
        (
            VideoDownloadJobStatus.RUNNING,
            "Iniciando…",
            True,
            False,
            VideoDownloadJobRowTone.NEUTRAL,
        ),
        (
            VideoDownloadJobStatus.CANCELLED,
            "Cancelado",
            False,
            True,
            VideoDownloadJobRowTone.NEUTRAL,
        ),
        (
            VideoDownloadJobStatus.COMPLETED,
            "Concluído",
            False,
            False,
            VideoDownloadJobRowTone.SUCCESS,
        ),
        (VideoDownloadJobStatus.FAILED, "Falhou", False, True, VideoDownloadJobRowTone.FAILURE),
    ],
)
def test_row_actions_and_labels_follow_the_job_status(
    video_download_job_status: VideoDownloadJobStatus,
    expected_status_label: str,
    can_cancel: bool,
    can_retry: bool,
    tone: VideoDownloadJobRowTone,
):
    row_view_model = build_video_download_job_row_view_model(
        build_job(video_download_job_status), None, None
    )

    assert row_view_model.video_download_job_identifier == SAMPLE_JOB_IDENTIFIER
    assert row_view_model.media_display_title_label == "Aula de Python"
    assert row_view_model.job_status_label == expected_status_label
    assert row_view_model.can_cancel_video_download_job is can_cancel
    assert row_view_model.can_retry_video_download_job is can_retry
    assert row_view_model.job_row_tone is tone


def test_running_row_shows_percentage_bar_and_details_from_latest_progress():
    row_view_model = build_video_download_job_row_view_model(
        build_job(VideoDownloadJobStatus.RUNNING),
        DownloadProgressSnapshot(40, 100, False, None, 3),
        None,
    )

    assert row_view_model.job_status_label == "40%"
    assert row_view_model.progress_bar_fraction == pytest.approx(0.4)
    assert row_view_model.job_detail_label == "40 B de 100 B   0:03 restantes"


def test_finished_rows_show_the_outcome_message_as_detail():
    row_view_model = build_video_download_job_row_view_model(
        build_job(VideoDownloadJobStatus.COMPLETED), None, "Aula [abc].mp4"
    )

    assert row_view_model.job_detail_label == "Aula [abc].mp4"
    assert row_view_model.progress_bar_fraction == 1.0


def test_untitled_job_falls_back_to_its_url():
    row_view_model = build_video_download_job_row_view_model(
        build_job(VideoDownloadJobStatus.QUEUED, media_display_title="  "), None, None
    )

    assert row_view_model.media_display_title_label == "https://youtu.be/abc"


def test_failed_row_hides_retry_when_retrying_cannot_help():
    row_view_model = build_video_download_job_row_view_model(
        build_job(VideoDownloadJobStatus.FAILED),
        None,
        "Sem permissão para gravar na pasta de destino.",
        failed_job_is_retryable=False,
    )

    assert row_view_model.can_retry_video_download_job is False


@pytest.mark.parametrize(
    ("video_download_job_status", "latest_progress_snapshot", "expected_indeterminate"),
    [
        (VideoDownloadJobStatus.RUNNING, None, True),
        (
            VideoDownloadJobStatus.RUNNING,
            DownloadProgressSnapshot(5, None, False, None, None),
            True,
        ),
        (VideoDownloadJobStatus.RUNNING, DownloadProgressSnapshot(5, 10, False, None, None), False),
        (VideoDownloadJobStatus.QUEUED, None, False),
        (VideoDownloadJobStatus.FAILED, None, False),
    ],
)
def test_ec08_only_running_jobs_without_known_total_animate_the_bar(
    video_download_job_status: VideoDownloadJobStatus,
    latest_progress_snapshot: DownloadProgressSnapshot | None,
    expected_indeterminate: bool,
):
    row_view_model = build_video_download_job_row_view_model(
        build_job(video_download_job_status), latest_progress_snapshot, None
    )

    assert row_view_model.is_progress_indeterminate is expected_indeterminate
