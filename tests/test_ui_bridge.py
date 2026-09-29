import time

from ui_bridge import UiEventBridge


def test_publishers_do_not_call_the_renderer_or_block():
    bridge = UiEventBridge(max_pending=2)

    started = time.monotonic()
    assert bridge.publish("biome", "WINDY")
    assert bridge.publish("biome", "RAINY")
    assert bridge.publish("status", "RUNNING")
    assert time.monotonic() - started < 0.1

    assert bridge.snapshot()["pending"] == 2
    assert bridge.snapshot()["coalesced"] == 1
    assert bridge.drain() == [
        {"event": "biome", "payload": "RAINY"},
        {"event": "status", "payload": "RUNNING"},
    ]
    assert bridge.snapshot()["delivered"] == 2
    bridge.stop()


def test_stalled_frontend_leaves_the_bounded_queue_available_for_recovery():
    bridge = UiEventBridge(max_pending=2)
    bridge.set_fault("bridge-stall")
    assert bridge.publish("biome", "CYBERSPACE")
    assert bridge.publish("status", "RUNNING")

    assert bridge.drain() == []
    assert bridge.snapshot()["pending"] == 2

    bridge.set_fault(None)
    assert bridge.drain() == [
        {"event": "biome", "payload": "CYBERSPACE"},
        {"event": "status", "payload": "RUNNING"},
    ]
    bridge.stop()
