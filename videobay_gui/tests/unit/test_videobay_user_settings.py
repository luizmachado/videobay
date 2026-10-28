from typing import Any

import pytest

from videobay_gui.core.videobay_user_settings import (
    DEFAULT_MAXIMUM_CONCURRENT_DOWNLOADS,
    OutputDirectoryProblem,
    VideobayUserSettings,
    describe_output_directory_problem_for_user,
    parse_videobay_user_settings_document,
    serialize_videobay_user_settings,
)

FALLBACK_OUTPUT_DIRECTORY = "/home/user/Downloads"
EXPLICIT_CONCURRENT_DOWNLOADS = 3


def test_round_trips_settings_through_serialized_document():
    original_settings = VideobayUserSettings(
        preferred_output_directory="/media/hd/videos",
        maximum_concurrent_downloads=EXPLICIT_CONCURRENT_DOWNLOADS,
    )

    assert (
        parse_videobay_user_settings_document(
            serialize_videobay_user_settings(original_settings), FALLBACK_OUTPUT_DIRECTORY
        )
        == original_settings
    )


@pytest.mark.parametrize(
    "partial_or_invalid_document",
    [
        {},
        {"preferred_output_directory": 42, "maximum_concurrent_downloads": "dois"},
        {"preferred_output_directory": "   ", "maximum_concurrent_downloads": 0},
        {"maximum_concurrent_downloads": 99},
        {"maximum_concurrent_downloads": True},
        [],
        "not a mapping",
        None,
    ],
)
def test_ec15_missing_or_invalid_fields_fall_back_to_defaults(partial_or_invalid_document: Any):
    parsed_settings = parse_videobay_user_settings_document(
        partial_or_invalid_document, FALLBACK_OUTPUT_DIRECTORY
    )

    assert parsed_settings == VideobayUserSettings(
        preferred_output_directory=FALLBACK_OUTPUT_DIRECTORY,
        maximum_concurrent_downloads=DEFAULT_MAXIMUM_CONCURRENT_DOWNLOADS,
    )


def test_keeps_valid_fields_when_others_are_invalid():
    parsed_settings = parse_videobay_user_settings_document(
        {"preferred_output_directory": "/srv/videos", "maximum_concurrent_downloads": -1},
        FALLBACK_OUTPUT_DIRECTORY,
    )

    assert parsed_settings.preferred_output_directory == "/srv/videos"
    assert parsed_settings.maximum_concurrent_downloads == DEFAULT_MAXIMUM_CONCURRENT_DOWNLOADS


@pytest.mark.parametrize("output_directory_problem", list(OutputDirectoryProblem))
def test_ec06_every_output_directory_problem_has_a_user_message(
    output_directory_problem: OutputDirectoryProblem,
):
    assert describe_output_directory_problem_for_user(output_directory_problem, "/x").strip()


def test_ec06_output_directory_message_names_the_folder():
    assert "/media/hd" in describe_output_directory_problem_for_user(
        OutputDirectoryProblem.OUTPUT_DIRECTORY_NOT_WRITABLE, "/media/hd"
    )
