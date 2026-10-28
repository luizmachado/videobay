import functools
from collections.abc import Callable
from typing import Any


class ManuallyDrainedBackgroundWorkerPoolFake:
    """Queues submitted tasks; tests decide when they run, which makes ordering races testable.

    Like the real adapter, callbacks (task results and posted UI callbacks) run in the order
    they were produced, after the tasks of the current drain have finished.
    """

    def __init__(self) -> None:
        self.pending_background_tasks: list[
            tuple[Callable[[], Any], Callable[[Any], None], Callable[[Exception], None]]
        ] = []
        self.pending_ui_thread_callbacks: list[Callable[[], None]] = []

    def submit_background_task[BackgroundTaskResult](
        self,
        background_task: Callable[[], BackgroundTaskResult],
        on_background_task_success: Callable[[BackgroundTaskResult], None],
        on_background_task_failure: Callable[[Exception], None],
    ) -> None:
        self.pending_background_tasks.append(
            (background_task, on_background_task_success, on_background_task_failure)
        )

    def post_callback_to_ui_thread(self, ui_thread_callback: Callable[[], None]) -> None:
        self.pending_ui_thread_callbacks.append(ui_thread_callback)

    def drain_pending_background_tasks(self) -> None:
        tasks_to_run_now = self.pending_background_tasks
        self.pending_background_tasks = []
        for background_task, on_success, on_failure in tasks_to_run_now:
            self.pending_ui_thread_callbacks.append(
                run_single_background_task_and_bind_callback(
                    background_task, on_success, on_failure
                )
            )
        ui_callbacks_to_run_now = self.pending_ui_thread_callbacks
        self.pending_ui_thread_callbacks = []
        for ui_thread_callback in ui_callbacks_to_run_now:
            ui_thread_callback()


def run_single_background_task_and_bind_callback(
    background_task: Callable[[], Any],
    on_background_task_success: Callable[[Any], None],
    on_background_task_failure: Callable[[Exception], None],
) -> Callable[[], None]:
    try:
        background_task_result = background_task()
    except Exception as background_task_error:
        # WHY: same pitfall as the real adapter: the `as` name is deleted when the except
        # block ends, so it must be bound now with partial, not captured by a lambda.
        return functools.partial(on_background_task_failure, background_task_error)
    return functools.partial(on_background_task_success, background_task_result)
