from dataclasses import replace

import pytest

from tests.unit.media_inspection_presenter_harness import (
    SAMPLE_VIDEO_URL,
    MediaInspectionPresenterTestHarness,
    build_sample_inspected_media_summary,
    presenter_harness,
)
from tests.unit.test_yt_dlp_metadata_extractor_adapter import build_adapter_with_scripted_client
from videobay_gui.core.inspected_media_summary import (
    PLAYLIST_SUBTITLE_LANGUAGE_OPTIONS,
    InspectedPlaylistEntry,
    build_inspected_media_summary_view_model,
    offered_subtitle_languages_for_summary,
)
from videobay_gui.core.media_quality_choice import BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
from videobay_gui.core.video_download_request import VideoDownloadRequest
from videobay_gui.core.yt_dlp_download_options_builder import build_yt_dlp_download_options

__all__ = ["presenter_harness"]


def test_adapter_collects_uploaded_subtitle_languages_but_not_live_chat():
    adapter, _ = build_adapter_with_scripted_client(
        {
            "title": "x",
            "subtitles": {"pt-BR": [{}], "en": [{}], "live_chat": [{}]},
            "automatic_captions": {"fr": [{}], "de": [{}]},
        }
    )

    inspected_media_summary = adapter.extract_inspected_media_summary(SAMPLE_VIDEO_URL)

    assert inspected_media_summary.available_subtitle_languages == ("en", "pt-BR")


def test_single_video_offers_its_own_languages_and_playlist_offers_common_ones():
    single_video_summary = replace(
        build_sample_inspected_media_summary(), available_subtitle_languages=("en", "pt-BR")
    )
    playlist_summary = replace(
        build_sample_inspected_media_summary(),
        inspected_playlist_entries=(InspectedPlaylistEntry(1, "Aula 1", 60, True),),
    )

    assert offered_subtitle_languages_for_summary(single_video_summary) == ("en", "pt-BR")
    assert offered_subtitle_languages_for_summary(playlist_summary) == (
        PLAYLIST_SUBTITLE_LANGUAGE_OPTIONS
    )
    assert build_inspected_media_summary_view_model(
        single_video_summary
    ).subtitle_language_options == (
        "en",
        "pt-BR",
    )


def test_selected_subtitle_languages_reach_the_download_selection_and_reset_on_new_inspection(
    presenter_harness: MediaInspectionPresenterTestHarness,
):
    presenter_harness.media_metadata_extractor_fake.script_media_summary(
        replace(build_sample_inspected_media_summary(), available_subtitle_languages=("en",))
    )
    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)
    inspection_presenter = presenter_harness.media_inspection_presenter

    inspection_presenter.handle_subtitle_language_selection_changed(("en",))
    selection_with_subtitles = inspection_presenter.current_download_selection()
    presenter_harness.inspect_media_url_and_drain_background(SAMPLE_VIDEO_URL)
    selection_after_new_inspection = inspection_presenter.current_download_selection()

    assert selection_with_subtitles is not None
    assert selection_with_subtitles.selected_subtitle_languages == ("en",)
    assert selection_after_new_inspection is not None
    assert selection_after_new_inspection.selected_subtitle_languages == ()


@pytest.mark.parametrize("is_ffmpeg_available", [True, False])
def test_builder_saves_chosen_subtitles_as_side_files_without_needing_ffmpeg(
    is_ffmpeg_available: bool,
):
    yt_dlp_download_options = build_yt_dlp_download_options(
        VideoDownloadRequest(
            "https://youtu.be/abc",
            BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
            "/d",
            selected_subtitle_languages=("pt-BR", "en"),
        ),
        is_ffmpeg_available,
    ).yt_dlp_download_options

    assert yt_dlp_download_options["writesubtitles"] is True
    assert yt_dlp_download_options["subtitleslangs"] == ["pt-BR", "en"]
    assert yt_dlp_download_options["subtitlesformat"] == "srt/vtt/best"


def test_builder_requests_no_subtitles_by_default():
    yt_dlp_download_options = build_yt_dlp_download_options(
        VideoDownloadRequest("https://youtu.be/abc", BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, "/d"),
        is_ffmpeg_available=True,
    ).yt_dlp_download_options

    assert "writesubtitles" not in yt_dlp_download_options
