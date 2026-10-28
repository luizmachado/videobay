from dataclasses import dataclass

from videobay_gui.core.inspected_media_summary import format_media_duration_for_display

INDETERMINATE_DOWNLOAD_PROGRESS_LABEL = "Baixando…"
BYTES_PER_BINARY_UNIT_STEP = 1024
# WHY: binary steps with the familiar "MB" label match what file managers on Linux show.
LARGER_BYTE_UNIT_LABELS = ("KB", "MB", "GB", "TB")


@dataclass(frozen=True)
class DownloadProgressSnapshot:
    downloaded_byte_count: int
    total_byte_count: int | None
    is_total_byte_count_estimated: bool
    download_speed_bytes_per_second: float | None
    estimated_seconds_remaining: int | None

    @property
    def completed_fraction(self) -> float | None:
        if not self.total_byte_count:
            return None
        # WHY: yt-dlp's estimated totals can be smaller than what actually arrives (EC-08).
        return min(self.downloaded_byte_count / self.total_byte_count, 1.0)


@dataclass(frozen=True)
class DownloadProgressViewModel:
    progress_bar_fraction: float | None
    progress_percentage_label: str
    progress_size_label: str
    progress_speed_label: str
    progress_remaining_time_label: str


def format_byte_count_for_display(byte_count: int | float) -> str:
    if byte_count < BYTES_PER_BINARY_UNIT_STEP:
        return f"{int(byte_count)} B"
    scaled_byte_count = float(byte_count)
    selected_unit_label = LARGER_BYTE_UNIT_LABELS[0]
    for larger_unit_label in LARGER_BYTE_UNIT_LABELS:
        if scaled_byte_count < BYTES_PER_BINARY_UNIT_STEP:
            break
        scaled_byte_count /= BYTES_PER_BINARY_UNIT_STEP
        selected_unit_label = larger_unit_label
    return f"{scaled_byte_count:.1f} {selected_unit_label}".replace(".", ",")


def build_download_progress_view_model(
    download_progress_snapshot: DownloadProgressSnapshot,
) -> DownloadProgressViewModel:
    completed_fraction = download_progress_snapshot.completed_fraction
    return DownloadProgressViewModel(
        progress_bar_fraction=completed_fraction,
        progress_percentage_label=(
            INDETERMINATE_DOWNLOAD_PROGRESS_LABEL
            if completed_fraction is None
            # WHY: floor, so the label never says 100% while bytes are still arriving.
            else f"{int(completed_fraction * 100)}%"
        ),
        progress_size_label=build_download_progress_size_label(download_progress_snapshot),
        progress_speed_label=(
            ""
            if download_progress_snapshot.download_speed_bytes_per_second is None
            else format_byte_count_for_display(
                download_progress_snapshot.download_speed_bytes_per_second
            )
            + "/s"
        ),
        progress_remaining_time_label=(
            ""
            if download_progress_snapshot.estimated_seconds_remaining is None
            else format_media_duration_for_display(
                download_progress_snapshot.estimated_seconds_remaining
            )
            + " restantes"
        ),
    )


def build_download_progress_size_label(download_progress_snapshot: DownloadProgressSnapshot) -> str:
    downloaded_label = format_byte_count_for_display(
        download_progress_snapshot.downloaded_byte_count
    )
    if not download_progress_snapshot.total_byte_count:
        return downloaded_label
    estimated_marker = "~" if download_progress_snapshot.is_total_byte_count_estimated else ""
    total_label = format_byte_count_for_display(download_progress_snapshot.total_byte_count)
    return f"{downloaded_label} de {estimated_marker}{total_label}"
