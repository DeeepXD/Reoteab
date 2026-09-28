import os
import tempfile
import threading
import time
import unittest
from unittest import mock

from requests.exceptions import ReadTimeout

from biome_tracker.biome_transitions import BiomeTransitionDispatcher
from biome_tracker.mixin_detection import DetectionMixin
from biome_tracker.mixin_webhook import WebhookMixin


class _StalledCaptureProcess:
    def __init__(self):
        self.started = False
        self.terminated = False

    def start(self):
        self.started = True

    def join(self, _timeout=None):
        pass

    def is_alive(self):
        return self.started and not self.terminated

    def terminate(self):
        self.terminated = True


class _CaptureResult:
    def __init__(self, status, detail):
        self.status = status
        self.detail = detail

    def poll(self):
        return True

    def recv(self):
        return self.status, self.detail

    def close(self):
        pass


class _CaptureContext:
    def __init__(self, status="stalled", detail="capture failed"):
        self.status = status
        self.detail = detail
        self.processes = []

    def Pipe(self, duplex=False):
        del duplex
        return _CaptureResult(self.status, self.detail), mock.Mock()

    def Process(self, **_kwargs):
        process = _StalledCaptureProcess()
        if self.status != "stalled":
            process.terminated = True
        self.processes.append(process)
        return process


class _DetectionHarness(DetectionMixin, WebhookMixin):
    def __init__(self):
        self.detection_running = True
        self._detection_generation = 1
        self._detection_thread_state = threading.local()
        self._detection_worker_health = {}
        self._detection_health_lock = threading.Lock()
        self._rare_screenshot_lock = threading.Lock()
        self._rare_screenshot_process_lock = threading.Lock()
        self._rare_screenshot_process = None
        self._biome_pipeline_state = {}
        self.current_biome = "NORMAL"
        self.config = {
            "webhook_url": "https://discord.invalid/webhook",
            "private_server_link": "",
            "biome_pings": {},
            "biome_notifier": {"NORMAL": "None", "CYBERSPACE": "Ping"},
            "rare_biome_screenshot": True,
            "record_rare_biome": False,
            "auto_pop_biomes": {},
        }
        self.biome_data = {
            "NORMAL": {"color": "0xffffff", "thumbnail_url": "https://example.invalid/normal.png"},
            "CYBERSPACE": {"color": "0x0A1A3D", "thumbnail_url": "https://example.invalid/cyberspace.png"},
        }
        self.biome_counts = {"NORMAL": 0, "CYBERSPACE": 0}
        self.biome_history = []
        self.last_sent = {}
        self.logs = []
        self.errors = []

    def append_log(self, message):
        self.logs.append(message)

    def error_logging(self, exception, custom_message=None, **_kwargs):
        self.errors.append((custom_message, exception))

    def save_config(self):
        pass

    def update_stats(self):
        pass

    def confirm_biome_popup(self, _biome):
        return None

    def activate_roblox_window(self):
        pass

    def is_roblox_focused(self):
        return True

    def is_fishing_mode_enabled(self):
        return False


class _RecordingDispatcher:
    def __init__(self):
        self.calls = []

    @property
    def pending_count(self):
        return len(self.calls)

    def submit(self, callback, *args, **_kwargs):
        self.calls.append((callback, args))
        return True


class BiomeReliabilityTests(unittest.TestCase):
    def test_current_rpc_text_extracts_cyberspace(self):
        line = (
            '2026-09-23T01:02:03.000Z [FLog::Output] [BloxstrapRPC] '
            '{"largeImage":{"assetId":"123","hoverText":"Cyberspace"}}\n'
        )
        self.assertEqual(DetectionMixin._extract_biome_from_rpc_line(line), "CYBERSPACE")

    def test_cyberspace_log_transition_reaches_dispatcher(self):
        harness = _DetectionHarness()
        harness._biome_transition_dispatcher = _RecordingDispatcher()
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, "Player.log")
            with open(log_path, "w", encoding="utf-8") as log:
                log.write(
                    '[BloxstrapRPC] {"largeImage":{"assetId":"123","hoverText":"CYBERSPACE"}}\n'
                )
            harness.logs_dir = directory
            harness.last_position = 0
            harness.get_latest_log_file = lambda: log_path
            harness.check_biome_in_logs()

        self.assertEqual(harness.current_biome, "CYBERSPACE")
        self.assertEqual(len(harness._biome_transition_dispatcher.calls), 1)
        _, args = harness._biome_transition_dispatcher.calls[0]
        self.assertEqual(args[:2], ("CYBERSPACE", "NORMAL"))

    def test_stalled_screenshot_is_terminated_and_later_capture_can_run(self):
        harness = _DetectionHarness()
        context = _CaptureContext()
        with tempfile.TemporaryDirectory() as directory:
            screenshot_path = os.path.join(directory, "cyberspace.png")
            with mock.patch("biome_tracker.mixin_detection.multiprocessing.get_context", return_value=context):
                started = time.monotonic()
                self.assertIsNone(harness._take_rare_biome_screenshot(screenshot_path, timeout=0.02))
                self.assertLess(time.monotonic() - started, 0.5)
                self.assertIsNone(harness._take_rare_biome_screenshot(screenshot_path, timeout=0.02))
                self.assertEqual(len(context.processes), 2)

        self.assertTrue(all(process.terminated for process in context.processes))
        self.assertTrue(any("timed out" in line for line in harness.logs))

    def test_stalled_screenshot_does_not_block_later_transitions_or_stop_recovery(self):
        harness = _DetectionHarness()
        context = _CaptureContext()
        dispatcher = BiomeTransitionDispatcher(1, harness._is_detection_session_active, harness.errors.append)
        harness._biome_transition_dispatcher = dispatcher
        completed = threading.Event()

        with (
            mock.patch("biome_tracker.mixin_detection.multiprocessing.get_context", return_value=context),
            mock.patch("biome_tracker.mixin_detection.time.sleep"),
        ):
            dispatcher.submit(harness.handle_biome_detection, "CYBERSPACE", "NORMAL", 1)
            dispatcher.submit(completed.set)
            self.assertTrue(completed.wait(1))
            harness._stop_rare_screenshot_capture()
            self.assertIsNone(harness._take_rare_biome_screenshot("later.png", timeout=0.02))

        self.assertEqual(len(context.processes), 2)
        self.assertTrue(all(process.terminated for process in context.processes))
        dispatcher.stop()
        dispatcher._worker.join(1)

    def test_screenshot_and_webhook_failures_do_not_stop_dispatcher(self):
        harness = _DetectionHarness()
        dispatcher = BiomeTransitionDispatcher(1, harness._is_detection_session_active, harness.errors.append)
        harness._biome_transition_dispatcher = dispatcher
        completed = threading.Event()

        failed_context = _CaptureContext(status="error", detail="capture failed")
        with (
            mock.patch("biome_tracker.mixin_detection.multiprocessing.get_context", return_value=failed_context),
            mock.patch("biome_tracker.mixin_webhook.requests.post", side_effect=ReadTimeout("webhook stalled")),
            mock.patch("biome_tracker.mixin_detection.time.sleep"),
        ):
            dispatcher.submit(harness.handle_biome_detection, "CYBERSPACE", "NORMAL", 1)
            dispatcher.submit(completed.set)
            self.assertTrue(completed.wait(1))

        self.assertTrue(dispatcher.is_alive)
        self.assertTrue(harness.detection_running)
        self.assertTrue(any("Error taking rare biome screenshot" == message for message, _ in harness.errors))
        self.assertTrue(any("Failed to send webhook" in line for line in harness.logs))
        dispatcher.stop()
        dispatcher._worker.join(1)

    def test_unexpected_worker_exit_is_visible_without_changing_session_state(self):
        harness = _DetectionHarness()
        harness._run_detection_worker(lambda: None, "Biome Check", 1)

        self.assertTrue(harness.detection_running)
        self.assertEqual(harness._detection_worker_health["Biome Check"]["state"], "failed")
        self.assertTrue(any("exited unexpectedly" in line for line in harness.logs))

    def test_old_worker_cannot_overwrite_new_generation_health(self):
        harness = _DetectionHarness()
        harness._detection_thread_state.generation = 2
        harness._mark_detection_worker("Biome Check", "running")
        harness._detection_thread_state.generation = 1
        harness._mark_detection_worker("Biome Check", "stopped")

        self.assertEqual(harness._detection_worker_health["Biome Check"]["generation"], 2)
        self.assertEqual(harness._detection_worker_health["Biome Check"]["state"], "running")

    def test_repeated_worker_sessions_do_not_accumulate_threads(self):
        harness = _DetectionHarness()
        workers = []

        for generation in range(1, 11):
            harness._detection_generation = generation
            harness.detection_running = True

            def loop(current_generation=generation):
                while harness._is_detection_session_active(current_generation):
                    time.sleep(0.005)

            worker = threading.Thread(
                target=harness._run_detection_worker,
                args=(loop, "Biome Check", generation),
            )
            workers.append(worker)
            worker.start()
            harness.detection_running = False
            worker.join(1)
            self.assertFalse(worker.is_alive())

        self.assertFalse(any(worker.is_alive() for worker in workers))


if __name__ == "__main__":
    unittest.main()
