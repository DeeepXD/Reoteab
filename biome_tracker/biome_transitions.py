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
    MAX_PENDING = 256
    RARE_RESERVED_PENDING = 32

    def __init__(self, generation: int, is_active: Callable[[int], bool], on_error: Callable[[Exception], None] | None = None, on_overflow: Callable[[int, str, bool], None] | None = None) -> None:
        self._generation = generation
        self._is_active = is_active
        self._on_error = on_error
        self._on_overflow = on_overflow
        self._stopped = threading.Event()
        self._state_lock = threading.Lock()
        self._overflow_reported = False
        self._queue: queue.Queue[tuple[Callable[..., Any], tuple[Any, ...]] | None] = queue.Queue(self.MAX_PENDING)
        self._worker = threading.Thread(target=self._run, name="Biome Transitions", daemon=True)
        self._worker.start()

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def is_alive(self) -> bool:
        return self._worker.is_alive()

    def submit(self, callback: Callable[..., Any], *args: Any, critical: bool = False, label: str = "transition") -> bool:
        with self._state_lock:
            if self._stopped.is_set():
                return False
            try:
                ordinary_limit = self.MAX_PENDING - self.RARE_RESERVED_PENDING
                if not critical and self._queue.qsize() >= ordinary_limit:
                    raise queue.Full
                self._queue.put_nowait((callback, args))
                self._overflow_reported = False
                return True
            except queue.Full:
                if self._on_overflow is not None and not self._overflow_reported:
                    self._overflow_reported = True
                    self._on_overflow(self._queue.qsize(), label, critical)
                return False

    def stop(self) -> None:
        with self._state_lock:
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
            self._queue.put_nowait(None)

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
