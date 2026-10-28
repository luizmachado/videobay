from typing import Protocol

from videobay_gui.core.inspected_media_summary import InspectedMediaSummaryViewModel


class MediaInspectionViewPort(Protocol):
    def show_media_url_validation_message(
        self, media_url_validation_message: str | None
    ) -> None: ...

    def set_inspect_media_url_action_enabled(self, is_inspect_action_enabled: bool) -> None: ...

    def show_media_inspection_in_progress(self) -> None: ...

    def show_inspected_media_summary(
        self, inspected_media_view_model: InspectedMediaSummaryViewModel
    ) -> None: ...

    def show_media_inspection_failure(
        self, media_inspection_failure_message: str, can_retry_media_inspection: bool
    ) -> None: ...

    def show_media_thumbnail_image(self, thumbnail_image_bytes: bytes) -> None: ...

    def show_media_thumbnail_placeholder(self) -> None: ...
