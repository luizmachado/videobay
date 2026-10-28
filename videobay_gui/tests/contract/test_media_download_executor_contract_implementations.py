from tests.contract.media_download_executor_port_contract import MediaDownloadExecutorPortContract
from tests.fakes.scripted_media_download_executor_fake import ScriptedMediaDownloadExecutorFake
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
