from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

DEFAULT_MAXIMUM_CONCURRENT_DOWNLOADS = 2
# WHY: more parallel downloads than this mostly triggers site rate limits (HTTP 429).
LARGEST_ALLOWED_CONCURRENT_DOWNLOADS = 8


@dataclass(frozen=True)
class VideobayUserSettings:
    preferred_output_directory: str
    maximum_concurrent_downloads: int = DEFAULT_MAXIMUM_CONCURRENT_DOWNLOADS


class OutputDirectoryProblem(StrEnum):
    OUTPUT_DIRECTORY_MISSING = "output_directory_missing"
    OUTPUT_PATH_IS_NOT_A_DIRECTORY = "output_path_is_not_a_directory"
    OUTPUT_DIRECTORY_NOT_WRITABLE = "output_directory_not_writable"


OUTPUT_DIRECTORY_PROBLEM_MESSAGE_TEMPLATES = {
    OutputDirectoryProblem.OUTPUT_DIRECTORY_MISSING: "A pasta {output_directory} não existe.",
    OutputDirectoryProblem.OUTPUT_PATH_IS_NOT_A_DIRECTORY: (
        "{output_directory} é um arquivo, não uma pasta."
    ),
    OutputDirectoryProblem.OUTPUT_DIRECTORY_NOT_WRITABLE: (
        "Sem permissão para gravar em {output_directory}. Escolha outra pasta."
    ),
}


def parse_videobay_user_settings_document(
    raw_settings_document: Any, fallback_output_directory: str
) -> VideobayUserSettings:
    # WHY: the file is user-editable (EC-15); every field is validated on its own so one bad
    # value never discards the others.
    if not isinstance(raw_settings_document, dict):
        return VideobayUserSettings(preferred_output_directory=fallback_output_directory)
    settings_document_fields = cast(dict[str, Any], raw_settings_document)
    return VideobayUserSettings(
        preferred_output_directory=parse_preferred_output_directory(
            settings_document_fields.get("preferred_output_directory"), fallback_output_directory
        ),
        maximum_concurrent_downloads=parse_maximum_concurrent_downloads(
            settings_document_fields.get("maximum_concurrent_downloads")
        ),
    )


def parse_preferred_output_directory(
    raw_preferred_output_directory: Any, fallback_output_directory: str
) -> str:
    if not isinstance(raw_preferred_output_directory, str):
        return fallback_output_directory
    return raw_preferred_output_directory.strip() or fallback_output_directory


def parse_maximum_concurrent_downloads(raw_maximum_concurrent_downloads: Any) -> int:
    # PROVENANCE: bool subclasses int in Python, so JSON `true` must be rejected explicitly.
    if isinstance(raw_maximum_concurrent_downloads, bool):
        return DEFAULT_MAXIMUM_CONCURRENT_DOWNLOADS
    if not isinstance(raw_maximum_concurrent_downloads, int):
        return DEFAULT_MAXIMUM_CONCURRENT_DOWNLOADS
    if not 1 <= raw_maximum_concurrent_downloads <= LARGEST_ALLOWED_CONCURRENT_DOWNLOADS:
        return DEFAULT_MAXIMUM_CONCURRENT_DOWNLOADS
    return raw_maximum_concurrent_downloads


def serialize_videobay_user_settings(
    videobay_user_settings: VideobayUserSettings,
) -> dict[str, Any]:
    return {
        "preferred_output_directory": videobay_user_settings.preferred_output_directory,
        "maximum_concurrent_downloads": videobay_user_settings.maximum_concurrent_downloads,
    }


def describe_output_directory_problem_for_user(
    output_directory_problem: OutputDirectoryProblem, output_directory: str
) -> str:
    return OUTPUT_DIRECTORY_PROBLEM_MESSAGE_TEMPLATES[output_directory_problem].format(
        output_directory=output_directory
    )
