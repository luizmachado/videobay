from collections.abc import Callable
from typing import Protocol


class BackgroundWorkerPoolPort(Protocol):
    def submit_background_task[BackgroundTaskResult](
        self,
        background_task: Callable[[], BackgroundTaskResult],
        on_background_task_success: Callable[[BackgroundTaskResult], None],
        on_background_task_failure: Callable[[Exception], None],
    ) -> None:
        """Runs background_task off the UI thread; both callbacks MUST run on the UI thread.

        PROVENANCE: ADR-0004 (Tkinter is not thread-safe).
        """
        ...

    def post_callback_to_ui_thread(self, ui_thread_callback: Callable[[], None]) -> None:
        """Callable from any thread; ui_thread_callback runs later on the UI thread, in order."""
        ...
