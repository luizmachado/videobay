import threading

from videobay_gui.adapters.threading_background_worker_pool_adapter import (
    ThreadingBackgroundWorkerPoolAdapter,
)


def test_task_runs_off_caller_thread_and_callback_waits_for_ui_drain():
    background_worker_pool = ThreadingBackgroundWorkerPoolAdapter()
    ui_thread_identifier = threading.get_ident()
    task_thread_identifiers: list[int] = []
    success_callback_thread_identifiers: list[int] = []
    delivered_task_results: list[str] = []

    def record_thread_and_return_result() -> str:
        task_thread_identifiers.append(threading.get_ident())
        return "inspected"

    def record_success_callback(task_result: str) -> None:
        success_callback_thread_identifiers.append(threading.get_ident())
        delivered_task_results.append(task_result)

    background_worker_pool.submit_background_task(
        record_thread_and_return_result, record_success_callback, lambda _error: None
    )
    background_worker_pool.shutdown_background_workers(wait_for_running_tasks=True)

    assert task_thread_identifiers[0] != ui_thread_identifier
    assert delivered_task_results == []

    assert background_worker_pool.drain_completed_callbacks_on_ui_thread() == 1
    assert delivered_task_results == ["inspected"]
    assert success_callback_thread_identifiers == [ui_thread_identifier]


def test_task_exception_is_delivered_to_failure_callback_on_drain():
    background_worker_pool = ThreadingBackgroundWorkerPoolAdapter()
    delivered_task_errors: list[Exception] = []

    def raise_network_error() -> str:
        raise ConnectionError("offline")

    background_worker_pool.submit_background_task(
        raise_network_error, lambda _result: None, delivered_task_errors.append
    )
    background_worker_pool.shutdown_background_workers(wait_for_running_tasks=True)
    background_worker_pool.drain_completed_callbacks_on_ui_thread()

    assert [str(task_error) for task_error in delivered_task_errors] == ["offline"]


def test_drain_with_nothing_completed_runs_no_callbacks():
    assert ThreadingBackgroundWorkerPoolAdapter().drain_completed_callbacks_on_ui_thread() == 0


def test_posted_ui_callback_waits_for_drain_and_keeps_order_with_task_results():
    background_worker_pool = ThreadingBackgroundWorkerPoolAdapter()
    delivered_ui_events: list[str] = []

    def post_progress_then_return() -> str:
        background_worker_pool.post_callback_to_ui_thread(lambda: delivered_ui_events.append("50%"))
        return "done"

    background_worker_pool.submit_background_task(
        post_progress_then_return, delivered_ui_events.append, lambda _error: None
    )
    background_worker_pool.shutdown_background_workers(wait_for_running_tasks=True)
    assert delivered_ui_events == []

    background_worker_pool.drain_completed_callbacks_on_ui_thread()

    assert delivered_ui_events == ["50%", "done"]
