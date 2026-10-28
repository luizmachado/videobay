import pytest

from videobay_gui.core.media_quality_choice import BEST_AVAILABLE_MEDIA_QUALITY_CHOICE
from videobay_gui.core.video_download_request import VideoDownloadRequest
from videobay_gui.core.yt_dlp_download_options_builder import (
    build_yt_dlp_download_options,
    compress_playlist_item_indices_to_yt_dlp_ranges,
)

SAMPLE_OUTPUT_DIRECTORY = "/home/user/Downloads"


def build_playlist_request(selected_playlist_item_indices: tuple[int, ...]) -> VideoDownloadRequest:
    return VideoDownloadRequest(
        "https://www.youtube.com/playlist?list=PL123",
        BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
        SAMPLE_OUTPUT_DIRECTORY,
        is_playlist_download=True,
        selected_playlist_item_indices=selected_playlist_item_indices,
    )


@pytest.mark.parametrize(
    ("playlist_item_indices", "expected_ranges"),
    [
        ((1,), "1"),
        ((1, 2, 3), "1-3"),
        ((7, 1, 3, 2, 9, 10), "1-3,7,9-10"),
        ((5, 5, 6), "5-6"),
    ],
)
def test_compresses_selected_indices_into_yt_dlp_ranges(
    playlist_item_indices: tuple[int, ...], expected_ranges: str
):
    assert compress_playlist_item_indices_to_yt_dlp_ranges(playlist_item_indices) == expected_ranges


def test_ec11_playlist_download_selects_items_and_keeps_going_past_broken_ones():
    yt_dlp_download_options = build_yt_dlp_download_options(
        build_playlist_request((1, 2, 5)), is_ffmpeg_available=True
    ).yt_dlp_download_options

    assert yt_dlp_download_options["playlist_items"] == "1-2,5"
    assert yt_dlp_download_options["ignoreerrors"] is True


def test_playlist_files_go_to_a_numbered_folder_named_after_the_playlist():
    yt_dlp_download_options = build_yt_dlp_download_options(
        build_playlist_request((1,)), is_ffmpeg_available=True
    ).yt_dlp_download_options

    assert yt_dlp_download_options["outtmpl"] == {
        "default": f"{SAMPLE_OUTPUT_DIRECTORY}/%(playlist_title)s/"
        "%(playlist_index)s - %(title)s [%(id)s]%(height& {}p|)s.%(ext)s"
    }


def test_whole_playlist_download_has_no_item_filter():
    yt_dlp_download_options = build_yt_dlp_download_options(
        build_playlist_request(()), is_ffmpeg_available=True
    ).yt_dlp_download_options

    assert "playlist_items" not in yt_dlp_download_options
    assert yt_dlp_download_options["ignoreerrors"] is True


def test_single_video_download_never_follows_a_playlist():
    yt_dlp_download_options = build_yt_dlp_download_options(
        VideoDownloadRequest("https://youtu.be/abc", BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, "/d"),
        is_ffmpeg_available=True,
    ).yt_dlp_download_options

    assert yt_dlp_download_options["noplaylist"] is True
    assert "ignoreerrors" not in yt_dlp_download_options
