# pyright: basic
# WHY: customtkinter has no type information, so strict mode would flag
# every widget call as Unknown.
# Views stay thin (ADR-0003); all logic lives in the strictly typed core.
import customtkinter

VIDEOBAY_MAIN_WINDOW_INITIAL_GEOMETRY = "720x480"


class VideobayMainWindowView(customtkinter.CTk):
    def __init__(self, videobay_main_window_title: str) -> None:
        super().__init__()
        customtkinter.set_appearance_mode("system")
        self.title(videobay_main_window_title)
        self.geometry(VIDEOBAY_MAIN_WINDOW_INITIAL_GEOMETRY)
        self.videobay_welcome_heading_label = customtkinter.CTkLabel(
            self,
            text=videobay_main_window_title,
            font=customtkinter.CTkFont(size=28, weight="bold"),
        )
        self.videobay_welcome_heading_label.pack(expand=True)

    def run_videobay_main_event_loop(self) -> None:
        self.mainloop()
