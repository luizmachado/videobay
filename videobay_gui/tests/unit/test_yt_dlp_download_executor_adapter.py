import errno
from pathlib import Path
from typing import Any, cast

import pytest
from yt_dlp.networking.exceptions import TransportError
from yt_dlp.utils import DownloadCancelled, PostProcessingError, UnavailableVideoError

from tests.fakes.scripted_yt_dlp_downloading_client_fake import (
    ScriptedYtDlpDownloadingClientFake,
    ScriptedYtDlpDownloadStep,
)
from tests.unit.test_yt_dlp_metadata_extractor_adapter import (
    build_yt_dlp_http_error,
    wrap_like_youtube_dl_extract_info,
)
from videobay_gui.adapters.yt_dlp_download_executor_adapter import (
    YtDlpDownloadExecutorAdapter,
    build_download_progress_snapshot_from_yt_dlp_hook,
    classify_yt_dlp_download_error,
)
from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.core.media_download_failure import (
    MediaDownloadCancelledError,
    MediaDownloadFailedError,
    MediaDownloadFailureKind,
)

SAMPLE_DOWNLOAD_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
SAMPLE_DOWNLOADED_BYTES = 512
SAMPLE_TOTAL_BYTES = 2048
SAMPLE_ETA_SECONDS = 12


def build_downloading_hook_payload(**extra_payload_fields: Any) -> dict[str, Any]:
    return {
        "status": "downloading",
        "downloaded_bytes": SAMPLE_DOWNLOADED_BYTES,
        **extra_payload_fields,
    }


def build_info_with_final_file(final_file_path: str) -> dict[str, Any]:
    return {"id": "jNQXAC9IVRw", "requested_downloads": [{"filepath": final_file_path}]}


def run_scripted_download(
    scripted_download_steps: list[ScriptedYtDlpDownloadStep],
    scripted_final_info_dict: dict[str, Any] | None = None,
    scripted_download_error: Exception | None = None,
    cancel_after_progress_count: int | None = None,
) -> tuple[Any, list[DownloadProgressSnapshot], ScriptedYtDlpDownloadingClientFake]:
    scripted_client = ScriptedYtDlpDownloadingClientFake(
        scripted_download_steps, scripted_final_info_dict, scripted_download_error
    )
    received_progress_snapshots: list[DownloadProgressSnapshot] = []
    media_download_outcome = YtDlpDownloadExecutorAdapter(
        scripted_client.build_from_yt_dlp_params
    ).execute_media_download(
        SAMPLE_DOWNLOAD_URL,
        {"format": "b"},
        received_progress_snapshots.append,
        lambda: (
            cancel_after_progress_count is not None
            and len(received_progress_snapshots) >= cancel_after_progress_count
        ),
    )
    return media_download_outcome, received_progress_snapshots, scripted_client


@pytest.mark.parametrize(
    ("hook_payload_fields", "expected_total", "expected_estimated"),
    [
        ({"total_bytes": SAMPLE_TOTAL_BYTES}, SAMPLE_TOTAL_BYTES, False),
        ({"total_bytes_estimate": 3000.7}, 3000, True),
        ({"total_bytes": None, "total_bytes_estimate": None}, None, False),
        ({}, None, False),
    ],
)
def test_ec08_maps_exact_estimated_and_missing_totals(
    hook_payload_fields: dict[str, Any], expected_total: int | None, expected_estimated: bool
):
    progress_snapshot = build_download_progress_snapshot_from_yt_dlp_hook(
        build_downloading_hook_payload(speed=1500.5, eta=SAMPLE_ETA_SECONDS, **hook_payload_fields)
    )

    assert progress_snapshot.downloaded_byte_count == SAMPLE_DOWNLOADED_BYTES
    assert progress_snapshot.total_byte_count == expected_total
    assert progress_snapshot.is_total_byte_count_estimated is expected_estimated
    assert progress_snapshot.download_speed_bytes_per_second == pytest.approx(1500.5)
    assert progress_snapshot.estimated_seconds_remaining == SAMPLE_ETA_SECONDS


def test_reports_progress_and_returns_final_paths_from_requested_downloads(tmp_path: Path):
    final_file_path = str(tmp_path / "Me at the zoo [jNQXAC9IVRw].mp4")

    media_download_outcome, received_progress_snapshots, _ = run_scripted_download(
        [build_downloading_hook_payload(total_bytes=SAMPLE_TOTAL_BYTES), {"status": "finished"}],
        build_info_with_final_file(final_file_path),
    )

    assert [snapshot.total_byte_count for snapshot in received_progress_snapshots] == [
        SAMPLE_TOTAL_BYTES
    ]
    assert media_download_outcome.downloaded_file_paths == (final_file_path,)
    assert media_download_outcome.was_already_downloaded is False


def test_ec07_no_downloading_events_means_file_already_existed(tmp_path: Path):
    media_download_outcome, received_progress_snapshots, _ = run_scripted_download(
        [{"status": "finished", "filename": str(tmp_path / "v.mp4")}],
        build_info_with_final_file(str(tmp_path / "v.mp4")),
    )

    assert received_progress_snapshots == []
    assert media_download_outcome.was_already_downloaded is True


def test_passes_quiet_params_hooks_and_never_overrides_caller_options():
    _, _, scripted_client = run_scripted_download([], build_info_with_final_file("/x.mp4"))

    received_params = scripted_client.received_yt_dlp_params
    assert received_params["format"] == "b"
    assert received_params["quiet"] is True
    assert received_params["noprogress"] is True
    assert len(received_params["progress_hooks"]) == 1
    assert received_params["logger"] is not None


def test_ec09_cancellation_raises_and_removes_partial_files(tmp_path: Path):
    partial_file = tmp_path / "Me at the zoo [jNQXAC9IVRw].mp4.part"
    unrelated_user_file = tmp_path / "Me at the zoo [jNQXAC9IVRw].mp4.notes.txt"
    unrelated_user_file.write_text("keep me")

    cancellation_download_steps: list[ScriptedYtDlpDownloadStep] = [
        lambda: partial_file.write_bytes(b"partial"),
        build_downloading_hook_payload(tmpfilename=str(partial_file)),
        lambda: (tmp_path / f"{partial_file.name}-Frag3").write_bytes(b"f"),
        build_downloading_hook_payload(tmpfilename=str(partial_file)),
    ]

    with pytest.raises(MediaDownloadCancelledError):
        run_scripted_download(
            cancellation_download_steps,
            scripted_download_error=DownloadCancelled(),
            cancel_after_progress_count=1,
        )

    assert sorted(path.name for path in tmp_path.iterdir()) == [unrelated_user_file.name]


def test_wraps_yt_dlp_failures_as_media_download_failed_error():
    with pytest.raises(MediaDownloadFailedError) as raised_failure:
        run_scripted_download(
            [], scripted_download_error=wrap_like_youtube_dl_extract_info(TransportError("reset"))
        )

    assert raised_failure.value.media_download_failure_kind == (
        MediaDownloadFailureKind.NETWORK_UNREACHABLE
    )


def raise_unavailable_video_error_from(os_error: OSError) -> UnavailableVideoError:
    try:
        raise os_error
    except OSError as caught_os_error:
        try:
            # PROVENANCE: yt-dlp hints `err` as str, but YoutubeDL.process_info passes the OSError.
            raise UnavailableVideoError(cast(Any, caught_os_error))
        except UnavailableVideoError as unavailable_video_error:
            return unavailable_video_error
    raise AssertionError("unreachable")


@pytest.mark.parametrize(
    ("raised_yt_dlp_error", "expected_media_download_failure_kind"),
    [
        (
            raise_unavailable_video_error_from(OSError(errno.ENOSPC, "No space left on device")),
            MediaDownloadFailureKind.OUTPUT_DISK_FULL,
        ),
        (
            raise_unavailable_video_error_from(PermissionError(errno.EACCES, "Permission denied")),
            MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE,
        ),
        (
            raise_unavailable_video_error_from(OSError(errno.EROFS, "Read-only file system")),
            MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE,
        ),
        (
            PostProcessingError("ffmpeg exited with code 1"),
            MediaDownloadFailureKind.POSTPROCESSING_FAILED,
        ),
        (
            wrap_like_youtube_dl_extract_info(build_yt_dlp_http_error(403)),
            MediaDownloadFailureKind.MEDIA_UNAVAILABLE,
        ),
        (
            wrap_like_youtube_dl_extract_info(build_yt_dlp_http_error(503)),
            MediaDownloadFailureKind.NETWORK_UNREACHABLE,
        ),
        (
            wrap_like_youtube_dl_extract_info(TransportError("timed out")),
            MediaDownloadFailureKind.NETWORK_UNREACHABLE,
        ),
        (
            UnavailableVideoError("Requested format is not available"),
            MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE,
        ),
    ],
)
def test_classifies_disk_permission_postprocessing_and_network_failures(
    raised_yt_dlp_error: Exception, expected_media_download_failure_kind: MediaDownloadFailureKind
):
    assert classify_yt_dlp_download_error(raised_yt_dlp_error) == (
        expected_media_download_failure_kind
    )


def test_passes_deno_path_to_downloads_too():
    scripted_client = ScriptedYtDlpDownloadingClientFake([], build_info_with_final_file("/x.mp4"))
    YtDlpDownloadExecutorAdapter(
        scripted_client.build_from_yt_dlp_params, deno_executable_path="/bundle/deno"
    ).execute_media_download(SAMPLE_DOWNLOAD_URL, {}, lambda _snapshot: None, lambda: False)

    assert scripted_client.received_yt_dlp_params["js_runtimes"] == {
        "deno": {"path": "/bundle/deno"}
    }
