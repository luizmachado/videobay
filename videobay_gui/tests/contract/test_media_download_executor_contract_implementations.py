import os
import shutil
from pathlib import Path

import pytest

from tests.contract.media_download_executor_port_contract import MediaDownloadExecutorPortContract
from tests.fakes.scripted_media_download_executor_fake import ScriptedMediaDownloadExecutorFake
from videobay_gui.adapters.yt_dlp_download_executor_adapter import YtDlpDownloadExecutorAdapter
from videobay_gui.core.download_progress_snapshot import DownloadProgressSnapshot
from videobay_gui.ports.media_download_executor_port import MediaDownloadExecutorPort

SCRIPTED_HALFWAY_PROGRESS = DownloadProgressSnapshot(
    downloaded_byte_count=50,
    total_byte_count=100,
    is_total_byte_count_estimated=False,
    download_speed_bytes_per_second=10.0,
    estimated_seconds_remaining=5,
)


class TestScriptedMediaDownloadExecutorFakeHonoursContract(MediaDownloadExecutorPortContract):
    def build_executor_under_contract(self) -> MediaDownloadExecutorPort:
        executor_fake = ScriptedMediaDownloadExecutorFake()
        executor_fake.scripted_progress_snapshots = [SCRIPTED_HALFWAY_PROGRESS]
        return executor_fake

    def downloadable_media_url(self) -> str:
        return "https://example.com/video"

    def download_options_for_contract(self) -> dict[str, object]:
        return {"format": "b"}


@pytest.mark.integration
class TestYtDlpDownloadExecutorAdapterHonoursContract(MediaDownloadExecutorPortContract):
    @pytest.fixture(autouse=True)
    def use_temporary_download_directory(self, tmp_path: Path) -> None:
        self.temporary_download_directory = tmp_path

    def build_executor_under_contract(self) -> MediaDownloadExecutorPort:
        # WHY: VIDEOBAY_CONTRACT_WITHOUT_DENO=1 lets us compare downloads with and without the
        # JS runtime (ADR-0008 follow-up) using the very same contract.
        use_deno = os.environ.get("VIDEOBAY_CONTRACT_WITHOUT_DENO") != "1"
        return YtDlpDownloadExecutorAdapter(
            deno_executable_path=shutil.which("deno") if use_deno else None
        )

    def downloadable_media_url(self) -> str:
        # PROVENANCE: "Me at the zoo" (19 s); its worst single-file format is well under 1 MB.
        return "https://www.youtube.com/watch?v=jNQXAC9IVRw"

    def download_options_for_contract(self) -> dict[str, object]:
        return {
            "format": "w",
            "outtmpl": {"default": str(self.temporary_download_directory / "%(id)s.%(ext)s")},
            "overwrites": False,
        }
