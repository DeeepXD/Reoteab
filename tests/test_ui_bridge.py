import threading
import time

from ui_bridge import UiEventBridge


class BlockingWindow:
    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()
        self.calls = []

    def evaluate_js(self, code):
        self.calls.append(code)
        self.entered.set()
        self.release.wait(2)


def test_blocked_renderer_does_not_block_publishers():
    bridge = UiEventBridge(max_pending=2)
    window = BlockingWindow()
    bridge.set_window(window)

    assert bridge.publish("biome", "first")
    assert window.entered.wait(1)

    started = time.monotonic()
    assert bridge.publish("biome", "latest")
    assert bridge.publish("status", "status")
    assert time.monotonic() - started < 0.1
    assert bridge.snapshot()["pending"] == 2

    window.release.set()
    deadline = time.monotonic() + 1
    while bridge.snapshot()["pending"] and time.monotonic() < deadline:
        time.sleep(0.01)

    assert "latest" in window.calls
    assert "status" in window.calls
    bridge.stop()


def test_bridge_coalesces_repeated_status_updates():
    bridge = UiEventBridge(max_pending=1)
    window = BlockingWindow()
    bridge.set_window(window)
    assert bridge.publish("status", "one")
    assert window.entered.wait(1)
    assert bridge.publish("status", "two")
    assert bridge.publish("status", "three")

    window.release.set()
    deadline = time.monotonic() + 1
    while bridge.snapshot()["pending"] and time.monotonic() < deadline:
        time.sleep(0.01)

    assert window.calls[-1] == "three"
    assert bridge.snapshot()["coalesced"] >= 1
    bridge.stop()
