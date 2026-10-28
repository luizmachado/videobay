import pytest

from tests.contract.media_metadata_extractor_port_contract import (
    MediaMetadataExtractorPortContract,
)
from tests.fakes.in_memory_media_metadata_extractor_fake import InMemoryMediaMetadataExtractorFake
from videobay_gui.adapters.yt_dlp_metadata_extractor_adapter import YtDlpMetadataExtractorAdapter
from videobay_gui.core.inspected_media_summary import InspectedMediaSummary
from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailedError,
    MediaInspectionFailureKind,
)
from videobay_gui.ports.media_metadata_extractor_port import MediaMetadataExtractorPort

# PROVENANCE: "Me at the zoo", the first YouTube upload. yt-dlp's own reference video
# (BaW_jenozKc) became unavailable in 2026-10, so the contract uses this long-lived one instead.
YT_DLP_REFERENCE_TEST_VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
SITE_WITHOUT_ANY_MEDIA_URL = "https://example.com/"


class TestInMemoryMediaMetadataExtractorFakeHonoursContract(MediaMetadataExtractorPortContract):
    def build_extractor_under_contract(self) -> MediaMetadataExtractorPort:
        extractor_fake = InMemoryMediaMetadataExtractorFake()
        extractor_fake.script_media_summary(
            InspectedMediaSummary(
                media_url=self.inspectable_media_url(),
                media_title="youtube-dl test video",
                media_uploader_name=None,
                media_duration_seconds=10,
                media_thumbnail_url=None,
                is_live_broadcast=False,
            )
        )
        extractor_fake.script_extraction_error(
            self.failing_media_url(),
            MediaInspectionFailedError(MediaInspectionFailureKind.UNSUPPORTED_SITE, "unsupported"),
        )
        return extractor_fake

    def inspectable_media_url(self) -> str:
        return YT_DLP_REFERENCE_TEST_VIDEO_URL

    def failing_media_url(self) -> str:
        return SITE_WITHOUT_ANY_MEDIA_URL


@pytest.mark.integration
class TestYtDlpMetadataExtractorAdapterHonoursContract(MediaMetadataExtractorPortContract):
    def build_extractor_under_contract(self) -> MediaMetadataExtractorPort:
        return YtDlpMetadataExtractorAdapter()

    def inspectable_media_url(self) -> str:
        return YT_DLP_REFERENCE_TEST_VIDEO_URL

    def failing_media_url(self) -> str:
        return SITE_WITHOUT_ANY_MEDIA_URL
