from dataclasses import dataclass

UNKNOWN_MEDIA_TITLE_LABEL = "Sem título"
UNKNOWN_MEDIA_UPLOADER_LABEL = "Autor desconhecido"
UNKNOWN_MEDIA_DURATION_LABEL = "Duração desconhecida"


@dataclass(frozen=True)
class InspectedMediaSummary:
    media_url: str
    media_title: str
    media_uploader_name: str | None
    media_duration_seconds: int | None
    media_thumbnail_url: str | None
    is_live_broadcast: bool


@dataclass(frozen=True)
class InspectedMediaSummaryViewModel:
    media_title_label: str
    media_uploader_label: str
    media_duration_label: str
    media_thumbnail_url: str | None


def format_media_duration_for_display(media_duration_seconds: int | None) -> str:
    if media_duration_seconds is None:
        return UNKNOWN_MEDIA_DURATION_LABEL
    duration_hours, remaining_seconds_after_hours = divmod(media_duration_seconds, 3600)
    duration_minutes, duration_seconds = divmod(remaining_seconds_after_hours, 60)
    if duration_hours:
        return f"{duration_hours}:{duration_minutes:02d}:{duration_seconds:02d}"
    return f"{duration_minutes}:{duration_seconds:02d}"


def build_inspected_media_summary_view_model(
    inspected_media_summary: InspectedMediaSummary,
) -> InspectedMediaSummaryViewModel:
    return InspectedMediaSummaryViewModel(
        media_title_label=inspected_media_summary.media_title.strip() or UNKNOWN_MEDIA_TITLE_LABEL,
        media_uploader_label=inspected_media_summary.media_uploader_name
        or UNKNOWN_MEDIA_UPLOADER_LABEL,
        media_duration_label=format_media_duration_for_display(
            inspected_media_summary.media_duration_seconds
        ),
        media_thumbnail_url=inspected_media_summary.media_thumbnail_url,
    )
