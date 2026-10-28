from dataclasses import dataclass
from enum import StrEnum


class AudioOutputCodec(StrEnum):
    MP3 = "mp3"
    M4A = "m4a"


@dataclass(frozen=True)
class MediaQualityChoice:
    maximum_video_height: int | None = None
    # WHY: audio-only is derived from the codec so the two can never contradict each other.
    audio_output_codec: AudioOutputCodec | None = None

    @property
    def is_audio_only(self) -> bool:
        return self.audio_output_codec is not None


BEST_AVAILABLE_MEDIA_QUALITY_CHOICE = MediaQualityChoice()
MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE = MediaQualityChoice(audio_output_codec=AudioOutputCodec.MP3)
M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE = MediaQualityChoice(audio_output_codec=AudioOutputCodec.M4A)

STANDARD_VIDEO_HEIGHT_TIERS = (4320, 2160, 1440, 1080, 720, 480, 360, 240, 144)
# WHY: encoders often crop a few lines (1080 → 1072), so heights up to 5% below a tier still
# count as that tier; anything further below drops to the next tier (800 → "Até 720p").
STANDARD_TIER_TOLERANCE_NUMERATOR = 21
STANDARD_TIER_TOLERANCE_DENOMINATOR = 20


def snap_video_height_to_standard_tier(raw_video_height: int) -> int | None:
    tolerant_video_height = raw_video_height * STANDARD_TIER_TOLERANCE_NUMERATOR
    for standard_video_height_tier in STANDARD_VIDEO_HEIGHT_TIERS:
        if (
            standard_video_height_tier * STANDARD_TIER_TOLERANCE_DENOMINATOR
            <= tolerant_video_height
        ):
            return standard_video_height_tier
    return None


def collect_existing_standard_tiers(available_video_heights: tuple[int, ...]) -> list[int]:
    snapped_video_height_tiers = {
        snap_video_height_to_standard_tier(raw_video_height)
        for raw_video_height in available_video_heights
    }
    return sorted(
        (
            video_height_tier
            for video_height_tier in snapped_video_height_tiers
            if video_height_tier
        ),
        reverse=True,
    )


def find_highest_available_standard_tier(available_video_heights: tuple[int, ...]) -> int | None:
    existing_standard_tiers = collect_existing_standard_tiers(available_video_heights)
    return existing_standard_tiers[0] if existing_standard_tiers else None


def build_media_quality_choices_for_available_heights(
    available_video_heights: tuple[int, ...],
) -> tuple[MediaQualityChoice, ...]:
    # WHY: the highest tier is already "Melhor (Np)", so listing it again would be a duplicate.
    lower_existing_standard_tiers = collect_existing_standard_tiers(available_video_heights)[1:]
    return (
        BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
        *(
            MediaQualityChoice(maximum_video_height=video_height_tier)
            for video_height_tier in lower_existing_standard_tiers
        ),
        MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
        M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    )


def describe_media_quality_choice_for_user(
    media_quality_choice: MediaQualityChoice, highest_available_tier: int | None
) -> str:
    if media_quality_choice.audio_output_codec is not None:
        return f"Só áudio ({media_quality_choice.audio_output_codec.upper()})"
    if media_quality_choice.maximum_video_height is not None:
        return f"Até {media_quality_choice.maximum_video_height}p"
    if highest_available_tier is None:
        return "Melhor qualidade"
    return f"Melhor ({highest_available_tier}p)"
