import queue
import threading
from collections.abc import Callable
from typing import Any


def biome_webhook_events(previous_biome: str | None, biome: str) -> list[tuple[str, str]]:
    if previous_biome == biome:
        return []

    events: list[tuple[str, str]] = []
    if previous_biome and previous_biome != "NORMAL":
        events.append((previous_biome, "end"))
    if biome != "NORMAL":
        events.append((biome, "start"))
    return events


class BiomeTransitionDispatcher:
    def __init__(self, generation: int, is_active: Callable[[int], bool], on_error: Callable[[Exception], None] | None = None) -> None:
        self._generation = generation
        self._is_active = is_active
        self._on_error = on_error
        self._stopped = threading.Event()
        self._queue: queue.Queue[tuple[Callable[..., Any], tuple[Any, ...]] | None] = queue.Queue()
        self._worker = threading.Thread(target=self._run, name="Biome Transitions", daemon=True)
        self._worker.start()

    def submit(self, callback: Callable[..., Any], *args: Any) -> None:
        if not self._stopped.is_set():
            self._queue.put((callback, args))

    def stop(self) -> None:
        if self._stopped.is_set():
            return
        self._stopped.set()
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
            else:
                self._queue.task_done()
        self._queue.put(None)

    def wait_for_idle(self) -> None:
        self._queue.join()

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    return
                callback, args = item
                if not self._stopped.is_set() and self._is_active(self._generation):
                    callback(*args)
            except Exception as exc:
                if self._on_error is not None:
                    self._on_error(exc)
            finally:
                self._queue.task_done()
