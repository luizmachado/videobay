import pytest

from videobay_gui.core.media_quality_choice import (
    BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
    build_media_quality_choices_for_available_heights,
    describe_media_quality_choice_for_user,
    snap_video_height_to_standard_tier,
)


@pytest.mark.parametrize(
    ("raw_video_height", "expected_standard_tier"),
    [
        (1080, 1080),
        (1072, 1080),
        (800, 720),
        (2160, 2160),
        (144, 144),
        (100, None),
    ],
)
def test_snaps_non_standard_heights_down_to_standard_tier(
    raw_video_height: int, expected_standard_tier: int | None
):
    assert snap_video_height_to_standard_tier(raw_video_height) == expected_standard_tier


def test_offers_best_then_lower_existing_tiers_then_audio_only():
    media_quality_choices = build_media_quality_choices_for_available_heights(
        (360, 1080, 720, 720, 480, 1072)
    )

    assert media_quality_choices == (
        BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
        MediaQualityChoice(maximum_video_height=720),
        MediaQualityChoice(maximum_video_height=480),
        MediaQualityChoice(maximum_video_height=360),
        MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
        M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    )


def test_never_offers_resolutions_that_do_not_exist():
    media_quality_choices = build_media_quality_choices_for_available_heights((480, 360))

    offered_maximum_heights = {choice.maximum_video_height for choice in media_quality_choices}
    assert offered_maximum_heights == {None, 360}
    assert describe_media_quality_choice_for_user(media_quality_choices[0], 480) == (
        "Melhor (480p)"
    )


@pytest.mark.parametrize("available_video_heights", [(), (90,)])
def test_audio_only_sources_still_offer_best_and_audio(available_video_heights: tuple[int, ...]):
    assert build_media_quality_choices_for_available_heights(available_video_heights) == (
        BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
        MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
        M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    )


@pytest.mark.parametrize(
    ("media_quality_choice", "highest_available_tier", "expected_label"),
    [
        (BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, 1080, "Melhor (1080p)"),
        (BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, None, "Melhor qualidade"),
        (MediaQualityChoice(maximum_video_height=720), 1080, "Até 720p"),
        (MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE, 1080, "Só áudio (MP3)"),
        (M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE, None, "Só áudio (M4A)"),
    ],
)
def test_describes_quality_choices_in_portuguese(
    media_quality_choice: MediaQualityChoice,
    highest_available_tier: int | None,
    expected_label: str,
):
    assert (
        describe_media_quality_choice_for_user(media_quality_choice, highest_available_tier)
        == expected_label
    )
