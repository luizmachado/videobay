from videobay_gui.core.inspected_media_summary import InspectedMediaSummary


class InMemoryMediaMetadataExtractorFake:
    """Answers from a URL → summary/exception table and records every requested URL."""

    def __init__(self) -> None:
        self.scripted_media_summaries_by_url: dict[str, InspectedMediaSummary] = {}
        self.scripted_extraction_errors_by_url: dict[str, Exception] = {}
        self.extracted_media_urls: list[str] = []

    def script_media_summary(self, inspected_media_summary: InspectedMediaSummary) -> None:
        self.scripted_media_summaries_by_url[inspected_media_summary.media_url] = (
            inspected_media_summary
        )

    def script_extraction_error(self, media_url: str, extraction_error: Exception) -> None:
        self.scripted_extraction_errors_by_url[media_url] = extraction_error

    def extract_inspected_media_summary(self, media_url: str) -> InspectedMediaSummary:
        self.extracted_media_urls.append(media_url)
        if media_url in self.scripted_extraction_errors_by_url:
            raise self.scripted_extraction_errors_by_url[media_url]
        return self.scripted_media_summaries_by_url[media_url]
