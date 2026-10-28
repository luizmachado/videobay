import pytest

from videobay_gui.core.download_progress_snapshot import (
    INDETERMINATE_DOWNLOAD_PROGRESS_LABEL,
    DownloadProgressSnapshot,
    build_download_progress_view_model,
    format_byte_count_for_display,
)

MEBIBYTE = 1024 * 1024


def build_progress_snapshot(
    downloaded_byte_count: int,
    total_byte_count: int | None,
    is_total_byte_count_estimated: bool = False,
    download_speed_bytes_per_second: float | None = None,
    estimated_seconds_remaining: int | None = None,
) -> DownloadProgressSnapshot:
    return DownloadProgressSnapshot(
        downloaded_byte_count=downloaded_byte_count,
        total_byte_count=total_byte_count,
        is_total_byte_count_estimated=is_total_byte_count_estimated,
        download_speed_bytes_per_second=download_speed_bytes_per_second,
        estimated_seconds_remaining=estimated_seconds_remaining,
    )


@pytest.mark.parametrize(
    ("byte_count", "expected_label"),
    [
        (0, "0 B"),
        (999, "999 B"),
        (1536, "1,5 KB"),
        (int(12.34 * MEBIBYTE), "12,3 MB"),
        (3 * 1024 * MEBIBYTE, "3,0 GB"),
        (2 * 1024**5, "2048,0 TB"),
    ],
)
def test_formats_byte_counts_with_brazilian_decimal_comma(byte_count: int, expected_label: str):
    assert format_byte_count_for_display(byte_count) == expected_label


@pytest.mark.parametrize(
    ("downloaded_byte_count", "total_byte_count", "expected_fraction"),
    [
        (25, 100, 0.25),
        (100, 100, 1.0),
        (150, 100, 1.0),
        (10, None, None),
        (10, 0, None),
    ],
)
def test_completed_fraction_is_clamped_and_unknown_without_total(
    downloaded_byte_count: int, total_byte_count: int | None, expected_fraction: float | None
):
    assert (
        build_progress_snapshot(downloaded_byte_count, total_byte_count).completed_fraction
        == expected_fraction
    )


def test_view_model_with_exact_total_shows_percentage_size_speed_and_eta():
    progress_view_model = build_download_progress_view_model(
        build_progress_snapshot(
            downloaded_byte_count=int(12.3 * MEBIBYTE),
            total_byte_count=45 * MEBIBYTE,
            download_speed_bytes_per_second=1.2 * MEBIBYTE,
            estimated_seconds_remaining=35,
        )
    )

    assert progress_view_model.progress_bar_fraction == pytest.approx(12.3 / 45, abs=1e-3)
    assert progress_view_model.progress_percentage_label == "27%"
    assert progress_view_model.progress_size_label == "12,3 MB de 45,0 MB"
    assert progress_view_model.progress_speed_label == "1,2 MB/s"
    assert progress_view_model.progress_remaining_time_label == "0:35 restantes"


def test_ec08_estimated_total_is_marked_with_tilde():
    progress_view_model = build_download_progress_view_model(
        build_progress_snapshot(
            downloaded_byte_count=5 * MEBIBYTE,
            total_byte_count=20 * MEBIBYTE,
            is_total_byte_count_estimated=True,
        )
    )

    assert progress_view_model.progress_size_label == "5,0 MB de ~20,0 MB"
    assert progress_view_model.progress_percentage_label == "25%"


def test_ec08_unknown_total_makes_progress_indeterminate():
    progress_view_model = build_download_progress_view_model(
        build_progress_snapshot(downloaded_byte_count=7 * MEBIBYTE, total_byte_count=None)
    )

    assert progress_view_model.progress_bar_fraction is None
    assert progress_view_model.progress_percentage_label == INDETERMINATE_DOWNLOAD_PROGRESS_LABEL
    assert progress_view_model.progress_size_label == "7,0 MB"
    assert progress_view_model.progress_speed_label == ""
    assert progress_view_model.progress_remaining_time_label == ""
