from collections.abc import Callable
from typing import Any


class FishingFailsafeTimer:
    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = float(timeout_seconds)
        self.started_at: float | None = None
        self.paused_at: float | None = None

    def start(self, now: float) -> None:
        self.started_at = float(now)
        self.paused_at = None

    def clear(self) -> None:
        self.started_at = None
        self.paused_at = None

    def pause(self, now: float) -> None:
        if self.started_at is not None and self.paused_at is None:
            self.paused_at = float(now)

    def resume(self, now: float) -> None:
        if self.started_at is not None and self.paused_at is not None:
            self.started_at += max(0.0, float(now) - self.paused_at)
        self.paused_at = None

    def expired(self, now: float) -> bool:
        return (
            self.started_at is not None
            and self.paused_at is None
            and (float(now) - self.started_at) >= self.timeout_seconds
        )

    def run_paused(
        self,
        action: Callable[[], Any],
        monotonic: Callable[[], float],
        set_active: Callable[[bool], None] | None = None,
    ) -> Any:
        self.pause(monotonic())
        try:
            if set_active is not None:
                set_active(True)
            return action()
        finally:
            self.resume(monotonic())
            if set_active is not None:
                set_active(False)
