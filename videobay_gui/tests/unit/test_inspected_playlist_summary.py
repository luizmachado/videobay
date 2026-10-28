from videobay_gui.core.inspected_media_summary import (
    InspectedMediaSummary,
    InspectedPlaylistEntry,
    build_inspected_media_summary_view_model,
    offered_media_quality_choices_for_summary,
)
from videobay_gui.core.media_quality_choice import MediaQualityChoice

SAMPLE_PLAYLIST_ENTRIES = (
    InspectedPlaylistEntry(1, "Aula 1", 600, True),
    InspectedPlaylistEntry(2, "[Private video]", None, False),
    InspectedPlaylistEntry(3, "Aula 3", 720, True),
)


def build_playlist_summary(
    inspected_playlist_entries: tuple[InspectedPlaylistEntry, ...] = SAMPLE_PLAYLIST_ENTRIES,
) -> InspectedMediaSummary:
    return InspectedMediaSummary(
        media_url="https://www.youtube.com/playlist?list=PL123",
        media_title="Curso de Python",
        media_uploader_name="Canal Dev",
        media_duration_seconds=None,
        media_thumbnail_url=None,
        is_live_broadcast=False,
        inspected_playlist_entries=inspected_playlist_entries,
    )


def test_summary_with_entries_is_a_playlist_and_single_video_is_not():
    assert build_playlist_summary().is_inspected_media_a_playlist
    assert not build_playlist_summary(()).is_inspected_media_a_playlist


def test_ec12_playlist_card_shows_item_count_instead_of_duration():
    playlist_view_model = build_inspected_media_summary_view_model(build_playlist_summary())

    assert playlist_view_model.media_duration_label == "Playlist · 3 vídeos"
    assert playlist_view_model.media_uploader_label == "Canal Dev"


def test_ec12_playlist_offers_common_height_caps_because_flat_listing_has_no_formats():
    offered_heights = [
        media_quality_choice.maximum_video_height
        for media_quality_choice in offered_media_quality_choices_for_summary(
            build_playlist_summary()
        )
        if not media_quality_choice.is_audio_only
    ]

    assert offered_heights == [None, 1080, 720, 480, 360]


def test_single_video_quality_choices_still_come_from_its_formats():
    single_video_summary = InspectedMediaSummary(
        media_url="https://youtu.be/abc",
        media_title="x",
        media_uploader_name=None,
        media_duration_seconds=10,
        media_thumbnail_url=None,
        is_live_broadcast=False,
        available_video_heights=(480,),
    )

    assert offered_media_quality_choices_for_summary(single_video_summary)[0] == (
        MediaQualityChoice()
    )
    assert len(offered_media_quality_choices_for_summary(single_video_summary)) == 3  # noqa: PLR2004
