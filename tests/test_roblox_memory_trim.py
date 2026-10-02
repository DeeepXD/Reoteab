from types import SimpleNamespace

from roblox_memory import RobloxMemoryTrimmer


class Process:
    def __init__(self, pid=123, rss=3 * 1024 * 1024 * 1024):
        self.pid = pid
        self.rss = rss

    def memory_info(self):
        return SimpleNamespace(rss=self.rss)


class Tracker:
    def __init__(self, process=None):
        self.config = {
            "roblox_memory_trim_enabled": True,
            "roblox_memory_trim_interval_minutes": "60",
            "roblox_memory_trim_threshold_mb": "2048",
        }
        self.detection_running = True
        self.reconnecting_state = False
        self.process = process
        self.logs = []

    def get_active_roblox_process(self):
        return self.process

    def append_log(self, message):
        self.logs.append(message)


def make_trimmer(tracker, empty):
    return RobloxMemoryTrimmer(tracker, clock=lambda: 10.0, sleeper=lambda _seconds: None, empty_working_set=empty)


def test_automatic_trim_respects_memory_threshold():
    process = Process(rss=1024 * 1024 * 1024)
    calls = []
    trimmer = make_trimmer(Tracker(process), lambda pid: calls.append(pid))

    result = trimmer._trim_once()

    assert result["status"] == "below-threshold"
    assert calls == []


def test_manual_trim_records_before_after_and_only_targets_active_roblox_process():
    process = Process(pid=456)
    calls = []

    def empty(pid):
        calls.append(pid)
        process.rss = 2200 * 1024 * 1024

    tracker = Tracker(process)
    trimmer = make_trimmer(tracker, empty)

    result = trimmer._trim_once(manual=True)

    assert calls == [456]
    assert result["status"] == "trimmed"
    assert result["before_rss"] == 3 * 1024 * 1024 * 1024
    assert result["after_rss"] == 2200 * 1024 * 1024
    assert result["reclaimed_rss"] > 0
    assert tracker.logs and "Roblox working set" in tracker.logs[-1]


def test_trim_skips_while_reconnecting_or_when_no_active_roblox_window_exists():
    calls = []
    tracker = Tracker(Process())
    tracker.reconnecting_state = True
    trimmer = make_trimmer(tracker, lambda pid: calls.append(pid))

    assert trimmer._trim_once(manual=True)["message"] == "Roblox is reconnecting."

    tracker.reconnecting_state = False
    tracker.process = None
    assert trimmer._trim_once(manual=True)["message"] == "Active Roblox window was not found."
    assert calls == []


def test_disabled_automatic_worker_does_not_trim():
    calls = []
    tracker = Tracker(Process())
    tracker.config["roblox_memory_trim_enabled"] = False
    trimmer = make_trimmer(tracker, lambda pid: calls.append(pid))

    assert trimmer._trim_once(manual=False)["status"] == "disabled"
    assert calls == []


def test_trim_records_a_single_follow_up_measurement():
    now = [10.0]
    process = Process(pid=456, rss=3 * 1024 * 1024 * 1024)

    def empty(_pid):
        process.rss = 2200 * 1024 * 1024

    trimmer = RobloxMemoryTrimmer(Tracker(process), clock=lambda: now[0], sleeper=lambda _seconds: None, empty_working_set=empty)
    trimmer._trim_once(manual=True)
    process.rss = 2400 * 1024 * 1024
    now[0] += 30

    trimmer._record_recheck()

    assert trimmer.snapshot()["follow_up_rss"] == 2400 * 1024 * 1024
    assert trimmer.snapshot()["returned_rss"] == 200 * 1024 * 1024
