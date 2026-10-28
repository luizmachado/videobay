import pytest

from videobay_gui.core.inspected_media_summary import (
    InspectedMediaSummary,
    build_inspected_media_summary_view_model,
    format_media_duration_for_display,
)
from videobay_gui.core.media_quality_choice import (
    AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
)


@pytest.mark.parametrize(
    ("media_duration_seconds", "expected_media_duration_label"),
    [
        (0, "0:00"),
        (5, "0:05"),
        (205, "3:25"),
        (3723, "1:02:03"),
        (36000, "10:00:00"),
        (None, "Duração desconhecida"),
    ],
)
def test_formats_media_duration_as_clock_text(
    media_duration_seconds: int | None, expected_media_duration_label: str
):
    assert format_media_duration_for_display(media_duration_seconds) == (
        expected_media_duration_label
    )


def test_view_model_exposes_title_uploader_duration_and_thumbnail():
    inspected_media_summary = InspectedMediaSummary(
        media_url="https://youtu.be/abc",
        media_title="Aula de Python",
        media_uploader_name="Canal Dev",
        media_duration_seconds=205,
        media_thumbnail_url="https://i.ytimg.com/abc.jpg",
        is_live_broadcast=False,
    )

    inspected_media_view_model = build_inspected_media_summary_view_model(inspected_media_summary)

    assert inspected_media_view_model.media_title_label == "Aula de Python"
    assert inspected_media_view_model.media_uploader_label == "Canal Dev"
    assert inspected_media_view_model.media_duration_label == "3:25"
    assert inspected_media_view_model.media_thumbnail_url == "https://i.ytimg.com/abc.jpg"


def test_view_model_uses_placeholders_when_metadata_is_missing():
    inspected_media_summary = InspectedMediaSummary(
        media_url="https://example.com/v",
        media_title="  ",
        media_uploader_name=None,
        media_duration_seconds=None,
        media_thumbnail_url=None,
        is_live_broadcast=False,
    )

    inspected_media_view_model = build_inspected_media_summary_view_model(inspected_media_summary)

    assert inspected_media_view_model.media_title_label == "Sem título"
    assert inspected_media_view_model.media_uploader_label == "Autor desconhecido"
    assert inspected_media_view_model.media_duration_label == "Duração desconhecida"
    assert inspected_media_view_model.media_thumbnail_url is None


def test_view_model_offers_quality_choices_with_matching_labels():
    inspected_media_summary = InspectedMediaSummary(
        media_url="https://youtu.be/abc",
        media_title="x",
        media_uploader_name=None,
        media_duration_seconds=None,
        media_thumbnail_url=None,
        is_live_broadcast=False,
        available_video_heights=(1080, 720, 360),
    )

    inspected_media_view_model = build_inspected_media_summary_view_model(inspected_media_summary)

    assert inspected_media_view_model.media_quality_choices == (
        BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
        MediaQualityChoice(maximum_video_height=720),
        MediaQualityChoice(maximum_video_height=360),
        AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    )
    assert inspected_media_view_model.media_quality_choice_labels == (
        "Melhor (1080p)",
        "Até 720p",
        "Até 360p",
        "Só áudio",
    )
