# pyright: basic
# WHY: customtkinter is untyped; this view stays thin (ADR-0003) and every decision lives in
# VideoDownloadQueuePresenter, which is strictly typed and fully unit tested.
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import filedialog

import customtkinter

from videobay_gui.core.video_download_job_row_view_model import (
    VideoDownloadJobRowTone,
    VideoDownloadJobRowViewModel,
)

NOTICE_TEXT_COLOR = ("#8a5300", "#ffcc80")
JOB_ROW_STATUS_TEXT_COLORS = {
    VideoDownloadJobRowTone.NEUTRAL: ("gray10", "gray90"),
    VideoDownloadJobRowTone.SUCCESS: ("#1b5e20", "#a5d6a7"),
    VideoDownloadJobRowTone.FAILURE: ("#b3261e", "#f2b8b5"),
}


@dataclass
class VideoDownloadJobRowWidgets:
    job_row_frame: customtkinter.CTkFrame
    title_label: customtkinter.CTkLabel
    status_label: customtkinter.CTkLabel
    progress_bar: customtkinter.CTkProgressBar
    detail_label: customtkinter.CTkLabel
    cancel_button: customtkinter.CTkButton
    retry_button: customtkinter.CTkButton


class VideoDownloadQueuePanelView(customtkinter.CTkFrame):
    """Folder picker, download button and the job list. Implements VideoDownloadQueueViewPort."""

    def __init__(self, master: customtkinter.CTk) -> None:
        super().__init__(master, corner_radius=12)
        self.on_output_directory_chosen: Callable[[str], None] = lambda _path: None
        self.on_download_requested: Callable[[], None] = lambda: None
        self.on_job_cancel_requested: Callable[[int], None] = lambda _job_identifier: None
        self.on_job_retry_requested: Callable[[int], None] = lambda _job_identifier: None
        self.job_row_widgets_by_identifier: dict[int, VideoDownloadJobRowWidgets] = {}
        self.build_output_directory_and_download_row()
        self.download_notice_label = customtkinter.CTkLabel(
            self, text="", text_color=NOTICE_TEXT_COLOR, anchor="w", justify="left", wraplength=700
        )
        self.download_notice_label.pack(fill="x", padx=12)
        self.job_list_frame = customtkinter.CTkScrollableFrame(self, label_text="Fila de downloads")
        self.job_list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def build_output_directory_and_download_row(self) -> None:
        action_row = customtkinter.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x", padx=12, pady=(12, 4))
        self.start_download_button = customtkinter.CTkButton(
            action_row, text="Baixar", width=110, command=lambda: self.on_download_requested()
        )
        self.start_download_button.pack(side="left")
        customtkinter.CTkLabel(action_row, text="Salvar em:").pack(side="left", padx=(16, 4))
        self.output_directory_label = customtkinter.CTkLabel(action_row, text="", anchor="w")
        self.output_directory_label.pack(side="left", fill="x", expand=True)
        self.choose_output_directory_button = customtkinter.CTkButton(
            action_row, text="Escolher pasta…", width=130, command=self.ask_output_directory
        )
        self.choose_output_directory_button.pack(side="right")

    def bind_video_download_queue_presenter_callbacks(
        self,
        on_output_directory_chosen: Callable[[str], None],
        on_download_requested: Callable[[], None],
        on_job_cancel_requested: Callable[[int], None],
        on_job_retry_requested: Callable[[int], None],
    ) -> None:
        self.on_output_directory_chosen = on_output_directory_chosen
        self.on_download_requested = on_download_requested
        self.on_job_cancel_requested = on_job_cancel_requested
        self.on_job_retry_requested = on_job_retry_requested

    def ask_output_directory(self) -> None:
        self.on_output_directory_chosen(
            filedialog.askdirectory(
                parent=self, initialdir=self.output_directory_label.cget("text")
            )
            or ""
        )

    def show_output_directory(self, output_directory: str) -> None:
        self.output_directory_label.configure(text=output_directory)

    def show_download_notice(self, download_notice_message: str | None) -> None:
        self.download_notice_label.configure(text=download_notice_message or "")

    def show_video_download_job_row(
        self, video_download_job_row_view_model: VideoDownloadJobRowViewModel
    ) -> None:
        job_identifier = video_download_job_row_view_model.video_download_job_identifier
        if job_identifier not in self.job_row_widgets_by_identifier:
            self.job_row_widgets_by_identifier[job_identifier] = self.build_job_row_widgets(
                job_identifier
            )
        job_row_widgets = self.job_row_widgets_by_identifier[job_identifier]
        job_row_widgets.title_label.configure(
            text=video_download_job_row_view_model.media_display_title_label
        )
        job_row_widgets.status_label.configure(
            text=video_download_job_row_view_model.job_status_label,
            text_color=JOB_ROW_STATUS_TEXT_COLORS[video_download_job_row_view_model.job_row_tone],
        )
        job_row_widgets.detail_label.configure(
            text=video_download_job_row_view_model.job_detail_label
        )
        self.show_job_row_progress(job_row_widgets, video_download_job_row_view_model)
        self.show_job_row_actions(job_row_widgets, video_download_job_row_view_model)

    def build_job_row_widgets(self, job_identifier: int) -> VideoDownloadJobRowWidgets:
        job_row_frame = customtkinter.CTkFrame(self.job_list_frame)
        job_row_frame.pack(fill="x", pady=4)
        job_row_frame.grid_columnconfigure(0, weight=1)
        title_label = customtkinter.CTkLabel(
            job_row_frame, text="", anchor="w", font=customtkinter.CTkFont(weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))
        status_label = customtkinter.CTkLabel(job_row_frame, text="", anchor="e", width=110)
        status_label.grid(row=0, column=1, sticky="e", padx=8, pady=(6, 0))
        progress_bar = customtkinter.CTkProgressBar(job_row_frame)
        progress_bar.set(0)
        progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=2)
        detail_label = customtkinter.CTkLabel(job_row_frame, text="", anchor="w")
        detail_label.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))
        action_frame = customtkinter.CTkFrame(job_row_frame, fg_color="transparent")
        action_frame.grid(row=2, column=1, sticky="e", padx=8, pady=(0, 6))
        cancel_button = customtkinter.CTkButton(
            action_frame,
            text="Cancelar",
            width=90,
            fg_color="transparent",
            border_width=1,
            command=lambda: self.on_job_cancel_requested(job_identifier),
        )
        retry_button = customtkinter.CTkButton(
            action_frame,
            text="Tentar de novo",
            width=120,
            command=lambda: self.on_job_retry_requested(job_identifier),
        )
        return VideoDownloadJobRowWidgets(
            job_row_frame,
            title_label,
            status_label,
            progress_bar,
            detail_label,
            cancel_button,
            retry_button,
        )

    def show_job_row_progress(
        self,
        job_row_widgets: VideoDownloadJobRowWidgets,
        video_download_job_row_view_model: VideoDownloadJobRowViewModel,
    ) -> None:
        progress_bar_fraction = video_download_job_row_view_model.progress_bar_fraction
        if video_download_job_row_view_model.is_progress_indeterminate:
            # WHY: EC-08. Without a known total the bar keeps animating instead of lying.
            job_row_widgets.progress_bar.configure(mode="indeterminate")
            job_row_widgets.progress_bar.start()
            return
        job_row_widgets.progress_bar.stop()
        job_row_widgets.progress_bar.configure(mode="determinate")
        job_row_widgets.progress_bar.set(progress_bar_fraction or 0)

    def show_job_row_actions(
        self,
        job_row_widgets: VideoDownloadJobRowWidgets,
        video_download_job_row_view_model: VideoDownloadJobRowViewModel,
    ) -> None:
        job_row_widgets.cancel_button.pack_forget()
        job_row_widgets.retry_button.pack_forget()
        if video_download_job_row_view_model.can_cancel_video_download_job:
            job_row_widgets.cancel_button.pack(side="right")
        if video_download_job_row_view_model.can_retry_video_download_job:
            job_row_widgets.retry_button.pack(side="right")
