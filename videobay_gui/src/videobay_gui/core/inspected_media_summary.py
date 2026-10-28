from dataclasses import dataclass

from videobay_gui.core.media_quality_choice import (
    BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
    build_media_quality_choices_for_available_heights,
    describe_media_quality_choice_for_user,
    find_highest_available_standard_tier,
)

UNKNOWN_MEDIA_TITLE_LABEL = "Sem título"
UNKNOWN_MEDIA_UPLOADER_LABEL = "Autor desconhecido"
UNKNOWN_MEDIA_DURATION_LABEL = "Duração desconhecida"
PLAYLIST_QUALITY_CAP_HEIGHTS = (1080, 720, 480, 360)
PLAYLIST_SUBTITLE_LANGUAGE_OPTIONS = ("pt", "en", "es")


@dataclass(frozen=True)
class InspectedPlaylistEntry:
    playlist_item_index: int
    playlist_entry_title: str
    playlist_entry_duration_seconds: int | None
    is_playlist_entry_available: bool


@dataclass(frozen=True)
class InspectedMediaSummary:
    media_url: str
    media_title: str
    media_uploader_name: str | None
    media_duration_seconds: int | None
    media_thumbnail_url: str | None
    is_live_broadcast: bool
    available_video_heights: tuple[int, ...] = ()
    inspected_playlist_entries: tuple[InspectedPlaylistEntry, ...] = ()
    available_subtitle_languages: tuple[str, ...] = ()

    @property
    def is_inspected_media_a_playlist(self) -> bool:
        return bool(self.inspected_playlist_entries)


@dataclass(frozen=True)
class InspectedMediaSummaryViewModel:
    media_title_label: str
    media_uploader_label: str
    media_duration_label: str
    media_thumbnail_url: str | None
    media_quality_choices: tuple[MediaQualityChoice, ...]
    media_quality_choice_labels: tuple[str, ...]
    subtitle_language_options: tuple[str, ...] = ()


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
    media_quality_choices = offered_media_quality_choices_for_summary(inspected_media_summary)
    # WHY: for a playlist the real best quality is unknown, so "Melhor" carries no height.
    highest_available_tier = (
        None
        if inspected_media_summary.is_inspected_media_a_playlist
        else find_highest_available_standard_tier(inspected_media_summary.available_video_heights)
    )
    return InspectedMediaSummaryViewModel(
        media_title_label=inspected_media_summary.media_title.strip() or UNKNOWN_MEDIA_TITLE_LABEL,
        media_uploader_label=inspected_media_summary.media_uploader_name
        or UNKNOWN_MEDIA_UPLOADER_LABEL,
        media_duration_label=(
            f"Playlist · {len(inspected_media_summary.inspected_playlist_entries)} vídeos"
            if inspected_media_summary.is_inspected_media_a_playlist
            else format_media_duration_for_display(inspected_media_summary.media_duration_seconds)
        ),
        media_thumbnail_url=inspected_media_summary.media_thumbnail_url,
        media_quality_choices=media_quality_choices,
        subtitle_language_options=offered_subtitle_languages_for_summary(inspected_media_summary),
        media_quality_choice_labels=tuple(
            describe_media_quality_choice_for_user(media_quality_choice, highest_available_tier)
            for media_quality_choice in media_quality_choices
        ),
    )


def offered_media_quality_choices_for_summary(
    inspected_media_summary: InspectedMediaSummary,
) -> tuple[MediaQualityChoice, ...]:
    # WHY: EC-12. The flat playlist listing has no formats, so a playlist offers common caps;
    # each video then falls back to its best format below the cap ("b[height<=N]"). Unlike a
    # single video, "Melhor" may be above 1080p here, so every cap is listed explicitly.
    if inspected_media_summary.is_inspected_media_a_playlist:
        return (
            BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
            *(
                MediaQualityChoice(maximum_video_height=playlist_cap_height)
                for playlist_cap_height in PLAYLIST_QUALITY_CAP_HEIGHTS
            ),
            MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
            M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
        )
    return build_media_quality_choices_for_available_heights(
        inspected_media_summary.available_video_heights
    )


def offered_subtitle_languages_for_summary(
    inspected_media_summary: InspectedMediaSummary,
) -> tuple[str, ...]:
    # WHY: EC-13. The flat playlist listing has no subtitle info, so playlists offer common
    # languages and items without them are simply skipped by yt-dlp.
    if inspected_media_summary.is_inspected_media_a_playlist:
        return PLAYLIST_SUBTITLE_LANGUAGE_OPTIONS
    return inspected_media_summary.available_subtitle_languages
