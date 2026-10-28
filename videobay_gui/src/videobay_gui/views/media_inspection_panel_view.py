# pyright: basic
# WHY: customtkinter and Pillow widgets are untyped; this view stays thin (ADR-0003) and every
# decision lives in MediaInspectionPresenter, which is strictly typed and fully unit tested.
import io
import tkinter
from collections.abc import Callable

import customtkinter
from PIL import Image, UnidentifiedImageError

from videobay_gui.core.inspected_media_summary import InspectedMediaSummaryViewModel

MEDIA_THUMBNAIL_DISPLAY_SIZE = (320, 180)
MEDIA_THUMBNAIL_PLACEHOLDER_TEXT = "Sem miniatura"
INSPECTION_IN_PROGRESS_TEXT = "Lendo informações do vídeo…"
MEDIA_URL_ENTRY_PLACEHOLDER_TEXT = "Cole aqui o endereço do vídeo ou playlist"
VALIDATION_MESSAGE_TEXT_COLOR = ("#b3261e", "#f2b8b5")


class MediaInspectionPanelView(customtkinter.CTkFrame):
    """URL bar + media card. Implements MediaInspectionViewPort."""

    def __init__(self, master: customtkinter.CTk) -> None:
        super().__init__(master, fg_color="transparent")
        self.on_media_url_text_changed: Callable[[str], None] = lambda _media_url_text: None
        self.on_inspect_media_url_requested: Callable[[str], None] = lambda _media_url_text: None
        self.on_media_quality_choice_selected: Callable[[int], None] = lambda _choice_index: None
        self.media_thumbnail_ctk_image: customtkinter.CTkImage | None = None
        self.build_media_url_bar_widgets()
        self.build_media_card_widgets()

    def build_media_url_bar_widgets(self) -> None:
        media_url_bar_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        media_url_bar_frame.pack(fill="x", padx=16, pady=(16, 4))
        self.media_url_text_variable = tkinter.StringVar(master=self)
        self.media_url_text_variable.trace_add("write", self.forward_media_url_text_change)
        self.media_url_entry = customtkinter.CTkEntry(
            media_url_bar_frame,
            textvariable=self.media_url_text_variable,
            placeholder_text=MEDIA_URL_ENTRY_PLACEHOLDER_TEXT,
            height=40,
        )
        self.media_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.media_url_entry.bind("<Return>", lambda _event: self.forward_inspect_request())
        self.inspect_media_url_button = customtkinter.CTkButton(
            media_url_bar_frame,
            text="Buscar",
            width=110,
            height=40,
            state="disabled",
            command=self.forward_inspect_request,
        )
        self.inspect_media_url_button.pack(side="right")
        self.media_url_validation_label = customtkinter.CTkLabel(
            self, text="", text_color=VALIDATION_MESSAGE_TEXT_COLOR, anchor="w"
        )
        self.media_url_validation_label.pack(fill="x", padx=20)

    def build_media_card_widgets(self) -> None:
        self.media_card_frame = customtkinter.CTkFrame(self, corner_radius=12)
        self.media_card_frame.pack(fill="x", padx=16, pady=12)
        self.media_thumbnail_label = customtkinter.CTkLabel(
            self.media_card_frame,
            text=MEDIA_THUMBNAIL_PLACEHOLDER_TEXT,
            width=MEDIA_THUMBNAIL_DISPLAY_SIZE[0],
            height=MEDIA_THUMBNAIL_DISPLAY_SIZE[1],
            fg_color=("gray85", "gray20"),
            corner_radius=8,
        )
        self.media_thumbnail_label.grid(row=0, column=0, rowspan=4, padx=12, pady=12, sticky="n")
        self.media_title_label = customtkinter.CTkLabel(
            self.media_card_frame,
            text="",
            font=customtkinter.CTkFont(size=18, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=360,
        )
        self.media_title_label.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(12, 2))
        self.media_details_label = customtkinter.CTkLabel(
            self.media_card_frame, text="", anchor="w", justify="left"
        )
        self.media_details_label.grid(row=1, column=1, sticky="ew", padx=(0, 12))
        self.media_quality_option_menu = customtkinter.CTkOptionMenu(
            self.media_card_frame,
            values=[""],
            state="disabled",
            command=self.forward_media_quality_choice_selection,
        )
        self.media_quality_option_menu.grid(row=2, column=1, sticky="w", padx=(0, 12), pady=8)
        self.retry_media_inspection_button = customtkinter.CTkButton(
            self.media_card_frame, text="Tentar de novo", command=self.forward_inspect_request
        )
        self.media_card_frame.grid_columnconfigure(1, weight=1)

    def bind_media_inspection_presenter_callbacks(
        self,
        on_media_url_text_changed: Callable[[str], None],
        on_inspect_media_url_requested: Callable[[str], None],
        on_media_quality_choice_selected: Callable[[int], None],
    ) -> None:
        self.on_media_url_text_changed = on_media_url_text_changed
        self.on_inspect_media_url_requested = on_inspect_media_url_requested
        self.on_media_quality_choice_selected = on_media_quality_choice_selected

    def forward_media_quality_choice_selection(self, selected_choice_label: str) -> None:
        offered_choice_labels = list(self.media_quality_option_menu.cget("values"))
        self.on_media_quality_choice_selected(offered_choice_labels.index(selected_choice_label))

    def forward_media_url_text_change(self, *_tk_trace_arguments: object) -> None:
        self.on_media_url_text_changed(self.media_url_text_variable.get())

    def forward_inspect_request(self) -> None:
        self.on_inspect_media_url_requested(self.media_url_text_variable.get())

    def show_media_url_validation_message(self, media_url_validation_message: str | None) -> None:
        self.media_url_validation_label.configure(text=media_url_validation_message or "")

    def set_inspect_media_url_action_enabled(self, is_inspect_action_enabled: bool) -> None:
        self.inspect_media_url_button.configure(
            state="normal" if is_inspect_action_enabled else "disabled"
        )

    def show_media_inspection_in_progress(self) -> None:
        self.retry_media_inspection_button.grid_remove()
        self.media_title_label.configure(text=INSPECTION_IN_PROGRESS_TEXT)
        self.media_details_label.configure(text="")
        self.media_quality_option_menu.configure(values=[""], state="disabled")
        self.media_quality_option_menu.set("")
        self.show_media_thumbnail_placeholder()

    def show_inspected_media_summary(
        self, inspected_media_view_model: InspectedMediaSummaryViewModel
    ) -> None:
        self.media_title_label.configure(text=inspected_media_view_model.media_title_label)
        self.media_details_label.configure(
            text=f"{inspected_media_view_model.media_uploader_label}"
            f"  ·  {inspected_media_view_model.media_duration_label}"
        )
        quality_choice_labels = list(inspected_media_view_model.media_quality_choice_labels)
        self.media_quality_option_menu.configure(values=quality_choice_labels, state="normal")
        self.media_quality_option_menu.set(quality_choice_labels[0])

    def show_media_inspection_failure(
        self, media_inspection_failure_message: str, can_retry_media_inspection: bool
    ) -> None:
        self.media_title_label.configure(text=media_inspection_failure_message)
        self.media_details_label.configure(text="")
        if can_retry_media_inspection:
            self.retry_media_inspection_button.grid(row=3, column=1, sticky="w", padx=(0, 12))
            return
        self.retry_media_inspection_button.grid_remove()

    def show_media_thumbnail_image(self, thumbnail_image_bytes: bytes) -> None:
        try:
            decoded_thumbnail_image = Image.open(io.BytesIO(thumbnail_image_bytes))
            decoded_thumbnail_image.thumbnail(MEDIA_THUMBNAIL_DISPLAY_SIZE)
        except (UnidentifiedImageError, OSError):
            # WHY: sites sometimes serve HTML or truncated files as thumbnails (EC-14).
            self.show_media_thumbnail_placeholder()
            return
        self.media_thumbnail_ctk_image = customtkinter.CTkImage(
            light_image=decoded_thumbnail_image,
            dark_image=decoded_thumbnail_image,
            size=decoded_thumbnail_image.size,
        )
        self.media_thumbnail_label.configure(image=self.media_thumbnail_ctk_image, text="")

    def show_media_thumbnail_placeholder(self) -> None:
        self.media_thumbnail_ctk_image = None
        self.media_thumbnail_label.configure(image=None, text=MEDIA_THUMBNAIL_PLACEHOLDER_TEXT)

    def selected_media_quality_choice_label(self) -> str:
        return self.media_quality_option_menu.get()
