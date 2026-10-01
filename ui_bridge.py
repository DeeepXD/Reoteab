from __future__ import annotations

import threading


class UiEventBridge:
    """Keeps presentation updates out of automation workers."""

    def __init__(self, max_pending: int = 64):
        self.max_pending = max(1, int(max_pending))
        self._lock = threading.Lock()
        self._pending: dict[str, object] = {}
        self._stopped = False
        self._accepted = 0
        self._coalesced = 0
        self._dropped = 0
        self._delivered = 0
        self._fault = None

    def set_window(self, _window) -> None:
        return

    def publish(self, event: str, payload=None) -> bool:
        key = str(event or "update")
        with self._lock:
            if self._stopped:
                return False
            if key in self._pending:
                self._coalesced += 1
            elif len(self._pending) >= self.max_pending:
                self._dropped += 1
                return False
            else:
                self._accepted += 1
            self._pending[key] = payload
        return True

    def drain(self) -> list[dict]:
        with self._lock:
            if self._fault == "bridge-stall":
                return []
            if self._fault == "drop-ui":
                self._dropped += len(self._pending)
                self._pending.clear()
                return []
            events = [{"event": event, "payload": payload} for event, payload in self._pending.items()]
            self._pending.clear()
            self._delivered += len(events)
            return events

    def set_fault(self, fault: str | None) -> None:
        with self._lock:
            self._fault = fault

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "pending": len(self._pending),
                "accepted": self._accepted,
                "coalesced": self._coalesced,
                "dropped": self._dropped,
                "delivered": self._delivered,
                "failed": 0,
                "blocked_for": 0.0,
                "worker_alive": False,
                "fault": self._fault,
            }

    def stop(self) -> None:
        with self._lock:
            self._stopped = True
            self._pending.clear()
