from collections.abc import Callable
from typing import Any


class ManuallyDrainedBackgroundWorkerPoolFake:
    """Queues submitted tasks; tests decide when they run, which makes ordering races testable."""

    def __init__(self) -> None:
        self.pending_background_tasks: list[
            tuple[Callable[[], Any], Callable[[Any], None], Callable[[Exception], None]]
        ] = []

    def submit_background_task[BackgroundTaskResult](
        self,
        background_task: Callable[[], BackgroundTaskResult],
        on_background_task_success: Callable[[BackgroundTaskResult], None],
        on_background_task_failure: Callable[[Exception], None],
    ) -> None:
        self.pending_background_tasks.append(
            (background_task, on_background_task_success, on_background_task_failure)
        )

    def drain_pending_background_tasks(self) -> None:
        tasks_to_run_now = self.pending_background_tasks
        self.pending_background_tasks = []
        for background_task, on_success, on_failure in tasks_to_run_now:
            run_single_background_task_with_callbacks(background_task, on_success, on_failure)


def run_single_background_task_with_callbacks(
    background_task: Callable[[], Any],
    on_background_task_success: Callable[[Any], None],
    on_background_task_failure: Callable[[Exception], None],
) -> None:
    try:
        background_task_result = background_task()
    except Exception as background_task_error:
        on_background_task_failure(background_task_error)
        return
    on_background_task_success(background_task_result)
