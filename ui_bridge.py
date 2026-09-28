from __future__ import annotations

import threading
import time


class UiEventBridge:
    """Keeps browser work out of automation workers."""

    def __init__(self, max_pending: int = 64):
        self.max_pending = max(1, int(max_pending))
        self._lock = threading.Lock()
        self._pending: dict[str, str] = {}
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._window = None
        self._accepted = 0
        self._coalesced = 0
        self._dropped = 0
        self._delivered = 0
        self._failed = 0
        self._blocked_since = None
        self._fault = None
        self._fault_release = threading.Event()
        self._fault_release.set()
        self._thread = threading.Thread(target=self._run, name="WebView Bridge", daemon=True)
        self._thread.start()

    def set_window(self, window) -> None:
        with self._lock:
            self._window = window

    def publish(self, event: str, js_code: str) -> bool:
        key = str(event or "update")
        with self._lock:
            if self._stop.is_set():
                return False
            if key in self._pending:
                self._coalesced += 1
            elif len(self._pending) >= self.max_pending:
                self._dropped += 1
                return False
            else:
                self._accepted += 1
            self._pending[key] = js_code
        self._wake.set()
        return True

    def set_fault(self, fault: str | None) -> None:
        with self._lock:
            self._fault = fault
            if fault == "bridge-stall":
                self._fault_release.clear()
            else:
                self._fault_release.set()

    def snapshot(self) -> dict:
        with self._lock:
            blocked_for = 0.0
            if self._blocked_since is not None:
                blocked_for = max(0.0, time.monotonic() - self._blocked_since)
            return {
                "pending": len(self._pending),
                "accepted": self._accepted,
                "coalesced": self._coalesced,
                "dropped": self._dropped,
                "delivered": self._delivered,
                "failed": self._failed,
                "blocked_for": round(blocked_for, 3),
                "worker_alive": self._thread.is_alive(),
                "fault": self._fault,
            }

    def stop(self) -> None:
        self._stop.set()
        self._fault_release.set()
        self._wake.set()

    def _next_event(self):
        with self._lock:
            if not self._pending:
                return None
            key = next(iter(self._pending))
            return self._pending.pop(key)

    def _run(self) -> None:
        while not self._stop.is_set():
            self._wake.wait(0.25)
            self._wake.clear()
            while not self._stop.is_set():
                js_code = self._next_event()
                if js_code is None:
                    break
                with self._lock:
                    window = self._window
                    self._blocked_since = time.monotonic()
                try:
                    with self._lock:
                        fault = self._fault
                    if fault == "bridge-stall":
                        self._fault_release.wait()
                    if fault == "drop-ui":
                        continue
                    if window is not None:
                        window.evaluate_js(js_code)
                        with self._lock:
                            self._delivered += 1
                except Exception:
                    with self._lock:
                        self._failed += 1
                finally:
                    with self._lock:
                        self._blocked_since = None
