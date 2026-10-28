from dataclasses import dataclass

from videobay_gui.core.media_quality_choice import (
    MediaQualityChoice,
    build_media_quality_choices_for_available_heights,
    describe_media_quality_choice_for_user,
    find_highest_available_standard_tier,
)

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
    available_video_heights: tuple[int, ...] = ()


@dataclass(frozen=True)
class InspectedMediaSummaryViewModel:
    media_title_label: str
    media_uploader_label: str
    media_duration_label: str
    media_thumbnail_url: str | None
    media_quality_choices: tuple[MediaQualityChoice, ...]
    media_quality_choice_labels: tuple[str, ...]


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
    media_quality_choices = build_media_quality_choices_for_available_heights(
        inspected_media_summary.available_video_heights
    )
    highest_available_tier = find_highest_available_standard_tier(
        inspected_media_summary.available_video_heights
    )
    return InspectedMediaSummaryViewModel(
        media_title_label=inspected_media_summary.media_title.strip() or UNKNOWN_MEDIA_TITLE_LABEL,
        media_uploader_label=inspected_media_summary.media_uploader_name
        or UNKNOWN_MEDIA_UPLOADER_LABEL,
        media_duration_label=format_media_duration_for_display(
            inspected_media_summary.media_duration_seconds
        ),
        media_thumbnail_url=inspected_media_summary.media_thumbnail_url,
        media_quality_choices=media_quality_choices,
        media_quality_choice_labels=tuple(
            describe_media_quality_choice_for_user(media_quality_choice, highest_available_tier)
            for media_quality_choice in media_quality_choices
        ),
    )
