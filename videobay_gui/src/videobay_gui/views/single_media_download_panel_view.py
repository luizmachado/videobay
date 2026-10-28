# pyright: basic
# WHY: customtkinter is untyped; this view stays thin (ADR-0003) and every decision lives in
# SingleMediaDownloadPresenter, which is strictly typed and fully unit tested.
from collections.abc import Callable
from tkinter import filedialog

import customtkinter

from videobay_gui.core.download_progress_snapshot import DownloadProgressViewModel

NOTICE_TEXT_COLOR = ("#8a5300", "#ffcc80")
FAILURE_TEXT_COLOR = ("#b3261e", "#f2b8b5")
SUCCESS_TEXT_COLOR = ("#1b5e20", "#a5d6a7")


class SingleMediaDownloadPanelView(customtkinter.CTkFrame):
    """Folder picker, download button and progress. Implements SingleMediaDownloadViewPort."""

    def __init__(self, master: customtkinter.CTk) -> None:
        super().__init__(master, corner_radius=12)
        self.on_output_directory_chosen: Callable[[str], None] = lambda _path: None
        self.on_download_requested: Callable[[], None] = lambda: None
        self.on_download_cancel_requested: Callable[[], None] = lambda: None
        self.on_download_retry_requested: Callable[[], None] = lambda: None
        self.build_output_directory_row()
        self.build_download_action_row()
        self.build_download_progress_widgets()

    def build_output_directory_row(self) -> None:
        output_directory_row = customtkinter.CTkFrame(self, fg_color="transparent")
        output_directory_row.pack(fill="x", padx=12, pady=(12, 4))
        customtkinter.CTkLabel(output_directory_row, text="Salvar em:").pack(side="left")
        self.output_directory_label = customtkinter.CTkLabel(
            output_directory_row, text="", anchor="w"
        )
        self.output_directory_label.pack(side="left", fill="x", expand=True, padx=8)
        self.choose_output_directory_button = customtkinter.CTkButton(
            output_directory_row,
            text="Escolher pasta…",
            width=130,
            command=self.ask_output_directory,
        )
        self.choose_output_directory_button.pack(side="right")

    def build_download_action_row(self) -> None:
        download_action_row = customtkinter.CTkFrame(self, fg_color="transparent")
        download_action_row.pack(fill="x", padx=12, pady=4)
        self.start_download_button = customtkinter.CTkButton(
            download_action_row,
            text="Baixar",
            width=130,
            command=lambda: self.on_download_requested(),
        )
        self.start_download_button.pack(side="left")
        self.cancel_download_button = customtkinter.CTkButton(
            download_action_row,
            text="Cancelar",
            width=110,
            fg_color="transparent",
            border_width=1,
            command=lambda: self.on_download_cancel_requested(),
        )
        self.retry_download_button = customtkinter.CTkButton(
            download_action_row,
            text="Tentar de novo",
            width=130,
            command=lambda: self.on_download_retry_requested(),
        )
        self.download_status_label = customtkinter.CTkLabel(
            download_action_row, text="", anchor="w", justify="left", wraplength=420
        )
        self.download_status_label.pack(side="right", fill="x", expand=True, padx=(12, 0))

    def build_download_progress_widgets(self) -> None:
        self.download_progress_bar = customtkinter.CTkProgressBar(self)
        self.download_progress_bar.set(0)
        self.download_progress_details_label = customtkinter.CTkLabel(self, text="", anchor="w")
        self.download_notice_label = customtkinter.CTkLabel(
            self, text="", text_color=NOTICE_TEXT_COLOR, anchor="w", justify="left", wraplength=640
        )
        self.download_notice_label.pack(fill="x", padx=12, pady=(0, 10))

    def bind_single_media_download_presenter_callbacks(
        self,
        on_output_directory_chosen: Callable[[str], None],
        on_download_requested: Callable[[], None],
        on_download_cancel_requested: Callable[[], None],
        on_download_retry_requested: Callable[[], None],
    ) -> None:
        self.on_output_directory_chosen = on_output_directory_chosen
        self.on_download_requested = on_download_requested
        self.on_download_cancel_requested = on_download_cancel_requested
        self.on_download_retry_requested = on_download_retry_requested

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

    def show_download_in_progress(self) -> None:
        self.start_download_button.configure(state="disabled")
        self.choose_output_directory_button.configure(state="disabled")
        self.retry_download_button.pack_forget()
        self.cancel_download_button.pack(side="left", padx=(8, 0))
        self.download_status_label.configure(text="Iniciando…", text_color=("gray10", "gray90"))
        self.download_progress_bar.pack(
            fill="x", padx=12, pady=(4, 2), before=self.download_notice_label
        )
        self.download_progress_details_label.pack(
            fill="x", padx=12, before=self.download_notice_label
        )
        self.download_progress_bar.configure(mode="indeterminate")
        self.download_progress_bar.start()
        self.download_progress_details_label.configure(text="")

    def show_download_progress(
        self, download_progress_view_model: DownloadProgressViewModel
    ) -> None:
        progress_bar_fraction = download_progress_view_model.progress_bar_fraction
        if progress_bar_fraction is None:
            # WHY: EC-08. Without a known total the bar keeps animating instead of lying.
            self.download_progress_bar.configure(mode="indeterminate")
        else:
            self.download_progress_bar.stop()
            self.download_progress_bar.configure(mode="determinate")
            self.download_progress_bar.set(progress_bar_fraction)
        self.download_status_label.configure(
            text=download_progress_view_model.progress_percentage_label
        )
        self.download_progress_details_label.configure(
            text="   ".join(
                progress_detail
                for progress_detail in (
                    download_progress_view_model.progress_size_label,
                    download_progress_view_model.progress_speed_label,
                    download_progress_view_model.progress_remaining_time_label,
                )
                if progress_detail
            )
        )

    def show_download_completed(self, download_completed_message: str) -> None:
        self.reset_download_controls_to_idle()
        self.download_progress_bar.configure(mode="determinate")
        self.download_progress_bar.set(1)
        self.download_status_label.configure(
            text=download_completed_message, text_color=SUCCESS_TEXT_COLOR
        )

    def show_download_failure(
        self, download_failure_message: str, can_retry_download: bool
    ) -> None:
        self.reset_download_controls_to_idle()
        self.download_status_label.configure(
            text=download_failure_message, text_color=FAILURE_TEXT_COLOR
        )
        if can_retry_download:
            self.retry_download_button.pack(side="left", padx=(8, 0))

    def show_download_cancelled(self) -> None:
        self.reset_download_controls_to_idle()
        self.download_progress_bar.pack_forget()
        self.download_progress_details_label.pack_forget()
        self.download_status_label.configure(
            text="Download cancelado.", text_color=("gray10", "gray90")
        )

    def reset_download_controls_to_idle(self) -> None:
        self.download_progress_bar.stop()
        self.cancel_download_button.pack_forget()
        self.start_download_button.configure(state="normal")
        self.choose_output_directory_button.configure(state="normal")
