from datetime import datetime

from biome_tracker.mixin_detection import DetectionMixin
from biome_tracker.mixin_session_report import SessionReportMixin
from biome_tracker.mixin_webhook import WebhookMixin


class ReportTracker(SessionReportMixin):
    def __init__(self):
        self._initialize_macro_report()


class WebhookReportTracker(SessionReportMixin, WebhookMixin):
    def __init__(self):
        self._initialize_macro_report()
        self.config = {"webhook_url": ["https://example.invalid/webhook"]}
        self.logged = []

    def get_webhook_list(self):
        return self.config["webhook_url"]

    def append_log(self, message):
        self.logged.append(message)

    def error_logging(self, *args):
        raise AssertionError(args)

    def format_seconds_to_hhmmss(self, seconds):
        return f"{seconds}s"


class StopTracker(SessionReportMixin):
    def __init__(self):
        self._initialize_macro_report()
        self.start_macro_report(datetime.now())
        self.detection_running = True
        self.lock = __import__("threading").Lock()
        self._biome_transition_dispatcher = None
        self._roblox_memory_trimmer = type("Trimmer", (), {"stop": lambda self: None})()
        self._detection_workers = []
        self.timer_paused_by_disconnect = False
        self.start_time = datetime.now()
        self.session_window_start = None
        self.saved_session = 0
        self.current_session = 0
        self.reports = []

    def _stop_rare_screenshot_capture(self):
        pass

    def _stop_player_logger_thread(self):
        pass

    def append_log(self, message):
        pass

    def set_title_threadsafe(self, title):
        pass

    def save_config(self):
        pass

    def send_macro_summary(self, last24h_seconds, reason_text="Macro stopped!", report=None):
        self.reports.append(report)


def test_macro_report_starts_fresh_for_each_run():
    tracker = ReportTracker()
    tracker.start_macro_report()
    tracker.record_macro_report_biome("RAINY")
    first = tracker.finish_macro_report()

    tracker.start_macro_report()
    second = tracker.finish_macro_report()

    assert first["biome_transitions"] == 1
    assert second["biome_transitions"] == 0
    assert second["rare_biomes"] == {}


def test_macro_report_persists_across_reconnect_and_tracks_recovery():
    tracker = ReportTracker()
    tracker.start_macro_report()
    tracker.record_macro_report_reconnect_attempt()
    tracker.record_macro_report_reconnect_attempt()
    tracker.record_macro_report_reconnect_recovery()
    tracker.record_macro_report_biome("CYBERSPACE")

    report = tracker.finish_macro_report()

    assert report["reconnect_attempts"] == 1
    assert report["reconnect_recoveries"] == 1
    assert report["rare_biomes"] == {"CYBERSPACE": 1}


def test_macro_report_records_only_reliable_event_counters():
    tracker = ReportTracker()
    tracker.start_macro_report()
    tracker.record_macro_report_biome("NORMAL")
    tracker.record_macro_report_biome("WINDY")
    tracker.record_macro_report_merchant("Rin")
    tracker.record_macro_report_failsafe("Fishing timeout")

    report = tracker.finish_macro_report()

    assert report["biome_transitions"] == 1
    assert report["merchants"] == {"Rin": 1}
    assert report["failsafes"] == {"Fishing timeout": 1}
    assert "fish_catches" not in report


def test_macro_report_is_finished_once_and_stop_uses_that_report():
    tracker = StopTracker()
    DetectionMixin.stop_detection(tracker)
    DetectionMixin.stop_detection(tracker)

    assert len(tracker.reports) == 1
    assert tracker.reports[0] is not None
    assert tracker.finish_macro_report() is None


def test_macro_report_webhook_does_not_send_twice(monkeypatch):
    tracker = WebhookReportTracker()
    tracker.start_macro_report()
    tracker.record_macro_report_biome("CYBERSPACE")
    report = tracker.finish_macro_report()
    sent = []

    class Response:
        def raise_for_status(self):
            pass

    def fake_post(url, json, timeout):
        sent.append(json)
        return Response()

    monkeypatch.setattr("biome_tracker.mixin_webhook.requests.post", fake_post)
    tracker.send_macro_summary(0, report=report)
    tracker.send_macro_summary(0)

    assert len(sent) == 1
    fields = sent[0]["embeds"][0]["fields"]
    assert any(field["name"] == "Rare biomes" for field in fields)
