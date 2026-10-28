import functools
import queue
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

# WHY: inspections and thumbnails are short network calls; downloads get their own pool (ADR-0004).
DEFAULT_MAXIMUM_BACKGROUND_THREADS = 4


class ThreadingBackgroundWorkerPoolAdapter:
    """Runs tasks on worker threads and parks their callbacks until the Tk thread drains them.

    PROVENANCE: ADR-0004. The Tk `after()` loop calls drain_completed_callbacks_on_ui_thread(),
    so no widget is ever touched from a worker thread.
    """

    def __init__(
        self, maximum_background_threads: int = DEFAULT_MAXIMUM_BACKGROUND_THREADS
    ) -> None:
        self.background_thread_executor = ThreadPoolExecutor(
            max_workers=maximum_background_threads, thread_name_prefix="videobay-background"
        )
        self.completed_callbacks_for_ui_thread: queue.SimpleQueue[Callable[[], None]] = (
            queue.SimpleQueue()
        )

    def submit_background_task[BackgroundTaskResult](
        self,
        background_task: Callable[[], BackgroundTaskResult],
        on_background_task_success: Callable[[BackgroundTaskResult], None],
        on_background_task_failure: Callable[[Exception], None],
    ) -> None:
        self.background_thread_executor.submit(
            self.run_background_task_and_park_callback,
            background_task,
            on_background_task_success,
            on_background_task_failure,
        )

    def run_background_task_and_park_callback[BackgroundTaskResult](
        self,
        background_task: Callable[[], BackgroundTaskResult],
        on_background_task_success: Callable[[BackgroundTaskResult], None],
        on_background_task_failure: Callable[[Exception], None],
    ) -> None:
        try:
            background_task_result = background_task()
        except Exception as background_task_error:
            # WHY: Python deletes the `as` name when the except block ends, so a lambda here
            # would raise NameError later on the UI thread; partial binds the error right now.
            self.completed_callbacks_for_ui_thread.put(
                functools.partial(on_background_task_failure, background_task_error)
            )
            return
        self.completed_callbacks_for_ui_thread.put(
            functools.partial(on_background_task_success, background_task_result)
        )

    def drain_completed_callbacks_on_ui_thread(self) -> int:
        drained_callback_count = 0
        while True:
            try:
                completed_callback = self.completed_callbacks_for_ui_thread.get_nowait()
            except queue.Empty:
                return drained_callback_count
            completed_callback()
            drained_callback_count += 1

    def shutdown_background_workers(self, wait_for_running_tasks: bool) -> None:
        self.background_thread_executor.shutdown(
            wait=wait_for_running_tasks, cancel_futures=not wait_for_running_tasks
        )
