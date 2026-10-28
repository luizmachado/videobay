from typing import Any, Self


class ScriptedYtDlpInfoExtractingClientFake:
    """Stands in for yt_dlp.YoutubeDL: records params and extract_info calls, returns a script."""

    def __init__(
        self,
        scripted_info_dict: dict[str, Any] | None,
        scripted_extraction_error: Exception | None = None,
    ) -> None:
        self.scripted_info_dict = scripted_info_dict
        self.scripted_extraction_error = scripted_extraction_error
        self.received_yt_dlp_params: dict[str, Any] = {}
        self.received_extract_info_calls: list[tuple[str, bool]] = []

    def build_from_yt_dlp_params(self, yt_dlp_params: dict[str, Any]) -> Self:
        self.received_yt_dlp_params = yt_dlp_params
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exception_details: object) -> None:
        return None

    def extract_info(self, url: str, download: bool = True) -> dict[str, Any] | None:
        self.received_extract_info_calls.append((url, download))
        if self.scripted_extraction_error is not None:
            raise self.scripted_extraction_error
        return self.scripted_info_dict
