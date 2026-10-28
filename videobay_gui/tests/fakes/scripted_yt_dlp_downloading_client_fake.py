from collections.abc import Callable
from typing import Any, Self

type ScriptedYtDlpDownloadStep = dict[str, Any] | Callable[[], object]


class ScriptedYtDlpDownloadingClientFake:
    """Stands in for yt_dlp.YoutubeDL during downloads.

    Each scripted step is either a progress-hook payload (passed to every progress hook, like
    yt-dlp does) or a callable run at that point (e.g. to create a .part file on disk).
    """

    def __init__(
        self,
        scripted_download_steps: list[ScriptedYtDlpDownloadStep],
        scripted_final_info_dict: dict[str, Any] | None = None,
        scripted_download_error: Exception | None = None,
    ) -> None:
        self.scripted_download_steps = scripted_download_steps
        self.scripted_final_info_dict = scripted_final_info_dict
        self.scripted_download_error = scripted_download_error
        self.received_yt_dlp_params: dict[str, Any] = {}

    def build_from_yt_dlp_params(self, yt_dlp_params: dict[str, Any]) -> Self:
        self.received_yt_dlp_params = yt_dlp_params
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exception_details: object) -> None:
        return None

    def extract_info(self, url: str, download: bool = True) -> dict[str, Any] | None:
        for scripted_download_step in self.scripted_download_steps:
            if callable(scripted_download_step):
                scripted_download_step()
                continue
            for progress_hook in self.received_yt_dlp_params.get("progress_hooks", []):
                progress_hook(scripted_download_step)
        if self.scripted_download_error is not None:
            raise self.scripted_download_error
        return self.scripted_final_info_dict
