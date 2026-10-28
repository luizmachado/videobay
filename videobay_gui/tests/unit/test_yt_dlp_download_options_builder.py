import pytest

from videobay_gui.core.media_quality_choice import (
    BEST_AVAILABLE_MEDIA_QUALITY_CHOICE,
    M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
    MediaQualityChoice,
)
from videobay_gui.core.video_download_request import VideoDownloadRequest
from videobay_gui.core.yt_dlp_download_options_builder import (
    FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE,
    FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE,
    build_yt_dlp_download_options,
    find_download_blocking_problem,
)

SAMPLE_OUTPUT_DIRECTORY = "/home/user/Vídeos"


def build_sample_video_download_request(
    media_quality_choice: MediaQualityChoice,
) -> VideoDownloadRequest:
    return VideoDownloadRequest(
        media_url="https://youtu.be/abc",
        media_quality_choice=media_quality_choice,
        output_directory=SAMPLE_OUTPUT_DIRECTORY,
    )


@pytest.mark.parametrize(
    ("media_quality_choice", "expected_format_selector"),
    [
        (BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, "bv*+ba/b"),
        (MediaQualityChoice(maximum_video_height=720), "bv*[height<=720]+ba/b[height<=720]"),
        (MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE, "ba/b"),
    ],
)
def test_with_ffmpeg_merges_best_video_and_audio_within_height_limit(
    media_quality_choice: MediaQualityChoice, expected_format_selector: str
):
    download_options_build_result = build_yt_dlp_download_options(
        build_sample_video_download_request(media_quality_choice), is_ffmpeg_available=True
    )

    assert download_options_build_result.yt_dlp_download_options["format"] == (
        expected_format_selector
    )
    assert download_options_build_result.ffmpeg_fallback_notice is None


def test_with_ffmpeg_prefers_mp4_container_then_mkv_when_merging():
    download_options_build_result = build_yt_dlp_download_options(
        build_sample_video_download_request(BEST_AVAILABLE_MEDIA_QUALITY_CHOICE),
        is_ffmpeg_available=True,
    )

    assert download_options_build_result.yt_dlp_download_options["merge_output_format"] == (
        "mp4/mkv"
    )


@pytest.mark.parametrize(
    ("media_quality_choice", "expected_format_selector"),
    [
        (BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, "b"),
        (MediaQualityChoice(maximum_video_height=480), "b[height<=480]/b"),
    ],
)
def test_ec04_without_ffmpeg_falls_back_to_single_file_formats_with_notice(
    media_quality_choice: MediaQualityChoice, expected_format_selector: str
):
    download_options_build_result = build_yt_dlp_download_options(
        build_sample_video_download_request(media_quality_choice), is_ffmpeg_available=False
    )

    assert download_options_build_result.yt_dlp_download_options["format"] == (
        expected_format_selector
    )
    assert "merge_output_format" not in download_options_build_result.yt_dlp_download_options
    assert download_options_build_result.ffmpeg_fallback_notice == (
        FFMPEG_MISSING_SINGLE_FILE_FALLBACK_NOTICE
    )


def test_output_template_puts_title_and_id_inside_chosen_directory():
    download_options_build_result = build_yt_dlp_download_options(
        build_sample_video_download_request(BEST_AVAILABLE_MEDIA_QUALITY_CHOICE),
        is_ffmpeg_available=True,
    )

    assert download_options_build_result.yt_dlp_download_options["outtmpl"] == {
        "default": f"{SAMPLE_OUTPUT_DIRECTORY}/%(title)s [%(id)s]%(height& {{}}p|)s.%(ext)s"
    }


def test_never_overwrites_existing_files():
    download_options_build_result = build_yt_dlp_download_options(
        build_sample_video_download_request(BEST_AVAILABLE_MEDIA_QUALITY_CHOICE),
        is_ffmpeg_available=True,
    )

    assert download_options_build_result.yt_dlp_download_options["overwrites"] is False


@pytest.mark.parametrize(
    ("audio_media_quality_choice", "expected_postprocessor"),
    [
        (
            MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"},
        ),
        (
            M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE,
            {"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": "0"},
        ),
    ],
)
def test_audio_only_extracts_audio_into_chosen_codec(
    audio_media_quality_choice: MediaQualityChoice, expected_postprocessor: dict[str, str]
):
    download_options_build_result = build_yt_dlp_download_options(
        build_sample_video_download_request(audio_media_quality_choice), is_ffmpeg_available=True
    )

    yt_dlp_download_options = download_options_build_result.yt_dlp_download_options
    assert yt_dlp_download_options["postprocessors"] == [expected_postprocessor]
    assert "merge_output_format" not in yt_dlp_download_options


def test_video_downloads_have_no_audio_extraction_postprocessor():
    download_options_build_result = build_yt_dlp_download_options(
        build_sample_video_download_request(BEST_AVAILABLE_MEDIA_QUALITY_CHOICE),
        is_ffmpeg_available=True,
    )

    assert "postprocessors" not in download_options_build_result.yt_dlp_download_options


@pytest.mark.parametrize(
    ("media_quality_choice", "is_ffmpeg_available", "expected_blocking_problem"),
    [
        (MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE, False, FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE),
        (M4A_AUDIO_ONLY_MEDIA_QUALITY_CHOICE, False, FFMPEG_REQUIRED_FOR_AUDIO_EXTRACTION_NOTICE),
        (MP3_AUDIO_ONLY_MEDIA_QUALITY_CHOICE, True, None),
        (BEST_AVAILABLE_MEDIA_QUALITY_CHOICE, False, None),
    ],
)
def test_ec05_audio_extraction_without_ffmpeg_is_blocked_with_install_instruction(
    media_quality_choice: MediaQualityChoice,
    is_ffmpeg_available: bool,
    expected_blocking_problem: str | None,
):
    assert (
        find_download_blocking_problem(
            build_sample_video_download_request(media_quality_choice), is_ffmpeg_available
        )
        == expected_blocking_problem
    )
    if expected_blocking_problem is not None:
        assert "apt install ffmpeg" in expected_blocking_problem
