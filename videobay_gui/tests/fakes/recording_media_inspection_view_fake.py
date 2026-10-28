from typing import Any

from videobay_gui.core.inspected_media_summary import InspectedMediaSummaryViewModel
from videobay_gui.core.playlist_item_page_view_model import PlaylistItemPageViewModel


class RecordingMediaInspectionViewFake:
    """Records every presenter → view call as (method_name, argument) tuples."""

    def __init__(self) -> None:
        self.recorded_view_calls: list[tuple[str, Any]] = []

    def show_media_url_validation_message(self, media_url_validation_message: str | None) -> None:
        self.recorded_view_calls.append(
            ("show_media_url_validation_message", media_url_validation_message)
        )

    def set_inspect_media_url_action_enabled(self, is_inspect_action_enabled: bool) -> None:
        self.recorded_view_calls.append(
            ("set_inspect_media_url_action_enabled", is_inspect_action_enabled)
        )

    def show_media_inspection_in_progress(self) -> None:
        self.recorded_view_calls.append(("show_media_inspection_in_progress", None))

    def show_inspected_media_summary(
        self, inspected_media_view_model: InspectedMediaSummaryViewModel
    ) -> None:
        self.recorded_view_calls.append(
            ("show_inspected_media_summary", inspected_media_view_model)
        )

    def show_media_inspection_failure(
        self, media_inspection_failure_message: str, can_retry_media_inspection: bool
    ) -> None:
        self.recorded_view_calls.append(
            (
                "show_media_inspection_failure",
                (media_inspection_failure_message, can_retry_media_inspection),
            )
        )

    def show_media_thumbnail_image(self, thumbnail_image_bytes: bytes) -> None:
        self.recorded_view_calls.append(("show_media_thumbnail_image", thumbnail_image_bytes))

    def show_media_thumbnail_placeholder(self) -> None:
        self.recorded_view_calls.append(("show_media_thumbnail_placeholder", None))

    def show_playlist_item_page(
        self, playlist_item_page_view_model: PlaylistItemPageViewModel | None
    ) -> None:
        self.recorded_view_calls.append(("show_playlist_item_page", playlist_item_page_view_model))

    def recorded_view_call_names(self) -> list[str]:
        return [view_call_name for view_call_name, _ in self.recorded_view_calls]

    def last_recorded_argument_of(self, view_call_name: str) -> Any:
        matching_view_call_arguments = [
            view_call_argument
            for recorded_call_name, view_call_argument in self.recorded_view_calls
            if recorded_call_name == view_call_name
        ]
        return matching_view_call_arguments[-1]
