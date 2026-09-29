from types import SimpleNamespace

from ui_maintenance import UiMaintenanceManager


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class FakeBridge:
    def __init__(self):
        self.paused = 0
        self.resumed = 0

    def pause_for_maintenance(self):
        self.paused += 1

    def resume_after_maintenance(self, _window):
        self.resumed += 1


class FakeWindow:
    def __init__(self):
        self.events = SimpleNamespace(loaded=SimpleNamespace(wait=lambda _timeout: True))


class FakeApi:
    def __init__(self):
        self._ui_bridge = FakeBridge()


def make_manager(clock):
    api = FakeApi()
    manager = UiMaintenanceManager(
        api,
        foreground_idle=600,
        background_idle=120,
        scheduled_interval=5400,
        cooldown=1,
        clock=clock,
    )
    calls = []
    manager.set_window(FakeWindow())
    manager.stop()
    manager._thread = object()
    manager._last_maintenance = -10_000
    return manager, calls


def test_active_foreground_ui_defers_maintenance():
    clock = Clock()
    manager, calls = make_manager(clock)
    manager._window_state = lambda: (True, False)
    manager.report_ui_state({"interaction": True, "active_page": "fishing"})
    manager._pending_reason = "sustained renderer growth"

    result = manager.run_once()

    assert result["status"] == "deferred"
    assert result["reason"] == "foreground activity"
    assert calls == []


def test_background_ui_defers_reload_when_the_runtime_cannot_safely_recreate_the_renderer():
    clock = Clock()
    manager, calls = make_manager(clock)
    manager._window_state = lambda: (False, False)
    manager.report_ui_state({"active_page": "presets", "theme": "neon", "scroll_y": 248, "interaction": True})
    clock.advance(121)
    manager._pending_reason = "scheduled maintenance"

    result = manager.run_once()

    assert result["status"] == "deferred"
    assert result["error"] == "Automatic WebView reload is unavailable in this pywebview runtime"
    assert calls == []
    assert manager.snapshot()["ui"]["last_deferred_reason"] == "safe renderer reload unavailable"


def test_unsaved_or_calibration_work_blocks_maintenance_even_when_background_idle():
    clock = Clock()
    manager, calls = make_manager(clock)
    manager._window_state = lambda: (False, True)
    manager.report_ui_state({"dirty": True, "active_page": "themedesign"})
    clock.advance(10_000)
    manager._pending_reason = "scheduled maintenance"

    assert manager.run_once()["reason"] == "unsaved changes"

    manager.report_ui_state({"dirty": False, "calibration": True})
    assert manager.run_once()["reason"] == "calibration"
    assert calls == []


def test_new_interaction_cancels_a_pending_maintenance_request():
    clock = Clock()
    manager, _calls = make_manager(clock)
    manager._window_state = lambda: (False, False)
    manager._pending_reason = "scheduled maintenance"
    clock.advance(121)

    assert manager._can_maintain(clock()) == (True, None)

    manager.report_ui_state({"interaction": True})
    assert manager.snapshot()["ui"]["pending_reason"] is None
    assert manager._can_maintain(clock()) == (False, "background activity")


def test_sustained_growth_requests_maintenance_but_short_spike_does_not():
    clock = Clock()
    manager, _calls = make_manager(clock)
    manager._window_state = lambda: (True, False)
    manager._last_maintenance = 0
    manager._samples.extend([
        {"total": 400 * 1024 * 1024, "renderer": 350 * 1024 * 1024, "processes": 2},
        {"total": 450 * 1024 * 1024, "renderer": 390 * 1024 * 1024, "processes": 2},
        {"total": 410 * 1024 * 1024, "renderer": 360 * 1024 * 1024, "processes": 2},
        {"total": 405 * 1024 * 1024, "renderer": 355 * 1024 * 1024, "processes": 2},
    ])
    clock.advance(100)
    assert manager._maintenance_reason_locked(clock()) is None

    manager._samples.clear()
    manager._samples.extend([
        {"total": 760 * 1024 * 1024, "renderer": 570 * 1024 * 1024, "processes": 2},
        {"total": 850 * 1024 * 1024, "renderer": 650 * 1024 * 1024, "processes": 2},
        {"total": 940 * 1024 * 1024, "renderer": 730 * 1024 * 1024, "processes": 2},
        {"total": 1_030 * 1024 * 1024, "renderer": 810 * 1024 * 1024, "processes": 2},
    ])
    assert manager._maintenance_reason_locked(clock()) == "sustained renderer growth"


