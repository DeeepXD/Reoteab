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
    def __init__(self, on_error: Callable[[Exception], None] | None = None) -> None:
        self._on_error = on_error
        self._queue: queue.Queue[tuple[Callable[..., Any], tuple[Any, ...]]] = queue.Queue()
        self._worker = threading.Thread(target=self._run, name="Biome Transitions", daemon=True)
        self._worker.start()

    def submit(self, callback: Callable[..., Any], *args: Any) -> None:
        self._queue.put((callback, args))

    def wait_for_idle(self) -> None:
        self._queue.join()

    def _run(self) -> None:
        while True:
            callback, args = self._queue.get()
            try:
                callback(*args)
            except Exception as exc:
                if self._on_error is not None:
                    self._on_error(exc)
            finally:
                self._queue.task_done()
