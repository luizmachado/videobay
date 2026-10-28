from dataclasses import replace

import pytest

from tests.unit.media_inspection_presenter_harness import (
    SAMPLE_VIDEO_URL,
    MediaInspectionPresenterTestHarness,
    build_sample_inspected_media_summary,
    presenter_harness,
)
from videobay_gui.core.media_quality_choice import (
    AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
)

__all__ = ["presenter_harness"]


def inspect_sample_video_with_heights(
    presenter_harness: MediaInspectionPresenterTestHarness, available_video_heights: tuple[int, ...]
) -> None:
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        replace(
            build_sample_inspected_media_summary(), available_video_heights=available_video_heights
        )
    )
    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)


def test_no_download_selection_before_any_successful_inspection(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    assert presenter_harness.media_inspection_presenter.current_download_selection() is None


def test_default_selection_is_best_quality_of_inspected_media(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_sample_video_with_heights(presenter_harness, (1080, 720))

    assert presenter_harness.media_inspection_presenter.current_download_selection() == (
        SAMPLE_VIDEO_URL,
        BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    )


@pytest.mark.parametrize(
    ("selected_choice_index", "expected_media_quality_choice"),
    [
        (1, MediaQualityChoice(maximum_video_height=720)),
        (2, AUDIO_ONLY_MEDIA_QUALITY_CHOICE),
        (99, BEST_AVAILABLE_MEDIA_QUALITY_CHOICE),
        (-1, BEST_AVAILABLE_MEDIA_QUALITY_CHOICE),
    ],
)
def test_selected_menu_index_maps_to_quality_choice(
    presenter_harness: MediaInspectionPresenterTestHarness,
    selected_choice_index: int,
    expected_media_quality_choice: MediaQualityChoice,
):
    inspect_sample_video_with_heights(presenter_harness, (1080, 720))

    presenter_harness.media_inspection_presenter.handle_media_quality_choice_selected(
        selected_choice_index
    )

    assert presenter_harness.media_inspection_presenter.current_download_selection() == (
        SAMPLE_VIDEO_URL,
        expected_media_quality_choice,
    )


def test_new_inspection_resets_selection_to_best(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    inspect_sample_video_with_heights(presenter_harness, (1080, 720))
    presenter_harness.media_inspection_presenter.handle_media_quality_choice_selected(2)

    inspect_sample_video_with_heights(presenter_harness, (480,))

    assert presenter_harness.media_inspection_presenter.current_download_selection() == (
        SAMPLE_VIDEO_URL,
        BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    )
