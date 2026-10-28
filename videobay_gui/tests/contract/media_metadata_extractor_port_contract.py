import pytest

from videobay_gui.core.media_inspection_failure import MediaInspectionFailedError
from videobay_gui.ports.media_metadata_extractor_port import MediaMetadataExtractorPort


class MediaMetadataExtractorPortContract:
    """Behaviour every MediaMetadataExtractorPort must share: the fake and the real yt-dlp adapter.

    Subclasses provide the extractor plus one inspectable URL and one URL that must fail.
    """

    def build_extractor_under_contract(self) -> MediaMetadataExtractorPort:
        raise NotImplementedError

    def inspectable_media_url(self) -> str:
        raise NotImplementedError

    def failing_media_url(self) -> str:
        raise NotImplementedError

    def test_summary_echoes_requested_url_and_has_title(self):
        extractor_under_contract = self.build_extractor_under_contract()

        inspected_media_summary = extractor_under_contract.extract_inspected_media_summary(
            self.inspectable_media_url()
        )

        assert inspected_media_summary.media_url == self.inspectable_media_url()
        assert inspected_media_summary.media_title.strip()

    def test_failures_surface_only_as_media_inspection_failed_error(self):
        extractor_under_contract = self.build_extractor_under_contract()

        with pytest.raises(MediaInspectionFailedError):
            extractor_under_contract.extract_inspected_media_summary(self.failing_media_url())
