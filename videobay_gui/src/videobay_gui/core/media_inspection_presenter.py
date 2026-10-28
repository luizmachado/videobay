from videobay_gui.core.inspected_media_summary import (
    InspectedMediaSummary,
    build_inspected_media_summary_view_model,
    offered_media_quality_choices_for_summary,
)
from videobay_gui.core.media_download_selection import MediaDownloadSelection
from videobay_gui.core.media_inspection_failure import (
    MediaInspectionFailedError,
    MediaInspectionFailureKind,
    describe_media_inspection_failure_for_user,
    is_media_inspection_failure_retryable,
)
from videobay_gui.core.media_url_syntax_validation import (
    MediaUrlRejectionReason,
    describe_media_url_rejection_reason_for_user,
    validate_media_url_syntax,
)
from videobay_gui.core.playlist_item_page_view_model import build_playlist_item_page_view_model
from videobay_gui.ports.background_worker_pool_port import BackgroundWorkerPoolPort
from videobay_gui.ports.media_inspection_view_port import MediaInspectionViewPort
from videobay_gui.ports.media_metadata_extractor_port import MediaMetadataExtractorPort
from videobay_gui.ports.thumbnail_image_fetcher_port import ThumbnailImageFetcherPort


class MediaInspectionPresenter:
    def __init__(
        self,
        media_inspection_view: MediaInspectionViewPort,
        media_metadata_extractor: MediaMetadataExtractorPort,
        background_worker_pool: BackgroundWorkerPoolPort,
        thumbnail_image_fetcher: ThumbnailImageFetcherPort,
    ) -> None:
        self.media_inspection_view = media_inspection_view
        self.media_metadata_extractor = media_metadata_extractor
        self.background_worker_pool = background_worker_pool
        self.thumbnail_image_fetcher = thumbnail_image_fetcher
        self.latest_inspected_media_summary: InspectedMediaSummary | None = None
        self.latest_requested_media_url: str | None = None
        self.selected_media_quality_choice_index = 0
        # WHY: None means "the default": every available item of the inspected playlist (EC-11).
        self.selected_playlist_item_indices: tuple[int, ...] | None = None
        self.selected_subtitle_languages: tuple[str, ...] = ()
        self.current_playlist_page_number = 1

    def handle_media_quality_choice_selected(self, selected_choice_index: int) -> None:
        self.selected_media_quality_choice_index = selected_choice_index

    def handle_playlist_page_requested(self, requested_page_number: int) -> None:
        self.current_playlist_page_number = requested_page_number
        self.render_playlist_item_page()

    def handle_playlist_item_checkbox_toggled(
        self, playlist_item_index: int, is_item_checked: bool
    ) -> None:
        inspected_playlist = self.inspected_playlist_or_none()
        if inspected_playlist is None:
            return
        selected_index_set = set(self.resolve_selected_playlist_items(inspected_playlist))
        if is_item_checked:
            selected_index_set.add(playlist_item_index)
        else:
            selected_index_set.discard(playlist_item_index)
        self.selected_playlist_item_indices = tuple(sorted(selected_index_set))
        self.render_playlist_item_page()

    def handle_all_playlist_items_toggled(self, should_check_every_item: bool) -> None:
        inspected_playlist = self.inspected_playlist_or_none()
        if inspected_playlist is None:
            return
        self.selected_playlist_item_indices = None if should_check_every_item else ()
        self.render_playlist_item_page()

    def inspected_playlist_or_none(self) -> InspectedMediaSummary | None:
        inspected_media_summary = self.latest_inspected_media_summary
        if (
            inspected_media_summary is None
            or not inspected_media_summary.is_inspected_media_a_playlist
        ):
            return None
        return inspected_media_summary

    def render_playlist_item_page(self) -> None:
        inspected_playlist = self.inspected_playlist_or_none()
        if inspected_playlist is None:
            return
        playlist_item_page_view_model = build_playlist_item_page_view_model(
            inspected_playlist.inspected_playlist_entries,
            self.resolve_selected_playlist_items(inspected_playlist),
            self.current_playlist_page_number,
        )
        self.current_playlist_page_number = playlist_item_page_view_model.current_page_number
        self.media_inspection_view.show_playlist_item_page(playlist_item_page_view_model)

    def handle_subtitle_language_selection_changed(
        self, selected_subtitle_languages: tuple[str, ...]
    ) -> None:
        self.selected_subtitle_languages = selected_subtitle_languages

    def handle_playlist_item_selection_changed(
        self, selected_playlist_item_indices: tuple[int, ...]
    ) -> None:
        self.selected_playlist_item_indices = selected_playlist_item_indices

    def current_download_selection(self) -> MediaDownloadSelection | None:
        inspected_media_summary = self.latest_inspected_media_summary
        if inspected_media_summary is None:
            return None
        offered_media_quality_choices = offered_media_quality_choices_for_summary(
            inspected_media_summary
        )
        selected_choice_index = self.selected_media_quality_choice_index
        # WHY: the menu is rebuilt on every inspection; a stale index falls back to "Melhor".
        if not 0 <= selected_choice_index < len(offered_media_quality_choices):
            selected_choice_index = 0
        return MediaDownloadSelection(
            inspected_media_summary.media_url,
            offered_media_quality_choices[selected_choice_index],
            inspected_media_summary.media_title,
            is_playlist_selection=inspected_media_summary.is_inspected_media_a_playlist,
            selected_playlist_item_indices_for_download=self.resolve_selected_playlist_items(
                inspected_media_summary
            ),
            selected_subtitle_languages=self.selected_subtitle_languages,
        )

    def resolve_selected_playlist_items(
        self, inspected_media_summary: InspectedMediaSummary
    ) -> tuple[int, ...]:
        if self.selected_playlist_item_indices is not None:
            return self.selected_playlist_item_indices
        return tuple(
            playlist_entry.playlist_item_index
            for playlist_entry in inspected_media_summary.inspected_playlist_entries
            if playlist_entry.is_playlist_entry_available
        )

    def handle_media_url_text_changed(self, raw_media_url: str) -> None:
        media_url_validation_outcome = validate_media_url_syntax(raw_media_url)
        self.media_inspection_view.show_media_url_validation_message(
            build_media_url_validation_message_for_view(
                media_url_validation_outcome.media_url_rejection_reason
            )
        )
        self.media_inspection_view.set_inspect_media_url_action_enabled(
            media_url_validation_outcome.is_media_url_acceptable
        )

    def handle_inspect_media_url_requested(self, raw_media_url: str) -> None:
        media_url_validation_outcome = validate_media_url_syntax(raw_media_url)
        if not media_url_validation_outcome.is_media_url_acceptable:
            self.handle_media_url_text_changed(raw_media_url)
            return
        requested_media_url = media_url_validation_outcome.normalized_media_url
        self.latest_requested_media_url = requested_media_url
        self.latest_inspected_media_summary = None
        self.media_inspection_view.show_media_inspection_in_progress()
        self.background_worker_pool.submit_background_task(
            lambda: self.media_metadata_extractor.extract_inspected_media_summary(
                requested_media_url
            ),
            lambda inspected_summary: self.handle_media_inspection_succeeded(
                requested_media_url, inspected_summary
            ),
            lambda inspection_error: self.handle_media_inspection_failed(
                requested_media_url, inspection_error
            ),
        )

    def handle_media_inspection_succeeded(
        self, requested_media_url: str, inspected_media_summary: InspectedMediaSummary
    ) -> None:
        if requested_media_url != self.latest_requested_media_url:
            return
        if inspected_media_summary.is_live_broadcast:
            self.show_media_inspection_failure_kind(
                MediaInspectionFailureKind.LIVE_BROADCAST_NOT_SUPPORTED
            )
            return
        self.latest_inspected_media_summary = inspected_media_summary
        self.selected_media_quality_choice_index = 0
        self.selected_playlist_item_indices = None
        self.selected_subtitle_languages = ()
        self.media_inspection_view.show_inspected_media_summary(
            build_inspected_media_summary_view_model(inspected_media_summary)
        )
        self.current_playlist_page_number = 1
        if inspected_media_summary.is_inspected_media_a_playlist:
            self.render_playlist_item_page()
        else:
            self.media_inspection_view.show_playlist_item_page(None)
        self.request_media_thumbnail_for_summary(inspected_media_summary)

    def request_media_thumbnail_for_summary(
        self, inspected_media_summary: InspectedMediaSummary
    ) -> None:
        media_thumbnail_url = inspected_media_summary.media_thumbnail_url
        if media_thumbnail_url is None:
            self.media_inspection_view.show_media_thumbnail_placeholder()
            return
        requested_media_url = inspected_media_summary.media_url
        self.background_worker_pool.submit_background_task(
            lambda: self.thumbnail_image_fetcher.fetch_thumbnail_image_bytes(media_thumbnail_url),
            lambda thumbnail_image_bytes: self.handle_media_thumbnail_fetched(
                requested_media_url, thumbnail_image_bytes
            ),
            # WHY: a thumbnail failure is cosmetic (EC-14); it never turns into an error message.
            lambda _thumbnail_fetch_error: self.handle_media_thumbnail_fetched(
                requested_media_url, None
            ),
        )

    def handle_media_thumbnail_fetched(
        self, requested_media_url: str, thumbnail_image_bytes: bytes | None
    ) -> None:
        if requested_media_url != self.latest_requested_media_url:
            return
        if thumbnail_image_bytes is None:
            self.media_inspection_view.show_media_thumbnail_placeholder()
            return
        self.media_inspection_view.show_media_thumbnail_image(thumbnail_image_bytes)

    def handle_media_inspection_failed(
        self, requested_media_url: str, media_inspection_error: Exception
    ) -> None:
        if requested_media_url != self.latest_requested_media_url:
            return
        if isinstance(media_inspection_error, MediaInspectionFailedError):
            self.show_media_inspection_failure_kind(
                media_inspection_error.media_inspection_failure_kind
            )
            return
        self.show_media_inspection_failure_kind(
            MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE
        )

    def show_media_inspection_failure_kind(
        self, media_inspection_failure_kind: MediaInspectionFailureKind
    ) -> None:
        self.media_inspection_view.show_media_inspection_failure(
            describe_media_inspection_failure_for_user(media_inspection_failure_kind),
            is_media_inspection_failure_retryable(media_inspection_failure_kind),
        )


def build_media_url_validation_message_for_view(
    media_url_rejection_reason: MediaUrlRejectionReason | None,
) -> str | None:
    if media_url_rejection_reason is None:
        return None
    # WHY: an empty box is the normal idle state, so it disables the button without an error.
    if media_url_rejection_reason is MediaUrlRejectionReason.EMPTY_MEDIA_URL:
        return None
    return describe_media_url_rejection_reason_for_user(media_url_rejection_reason)
