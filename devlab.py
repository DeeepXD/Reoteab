from __future__ import annotations

import csv
import json
import os
import shutil
import sys
import threading
import time
import traceback
from collections import deque
from datetime import datetime
from pathlib import Path

import psutil


class DevLabDiagnostics:
    MAX_SAMPLES = 1800
    MAX_PIPELINE_EVENTS = 500

    def __init__(self, api):
        self.api = api
        self._samples = deque(maxlen=self.MAX_SAMPLES)
        self._pipeline = deque(maxlen=self.MAX_PIPELINE_EVENTS)
        self._latest_sample = {}
        self._lock = threading.Lock()
        self._recording = False
        self._stop = threading.Event()
        self._thread = None
        self._stress_stop = threading.Event()
        self._stress_thread = None
        self._replay_stop = threading.Event()
        self._replay_thread = None
        self._replay_lock = threading.Lock()
        self._replay = {"active": False, "events": 0, "transitions": 0, "attachments": 0, "failed": 0}
        self._mock_webhook_mode = "success"
        self._fault = None
        self._thread_stacks = []

    def start_recording(self):
        if self._recording:
            return self.snapshot()
        self._recording = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._sample_loop, name="DevLab Profiler", daemon=True)
        self._thread.start()
        return self.snapshot()

    def stop_recording(self):
        self._recording = False
        self._stop.set()
        return self.snapshot()

    def _sample_loop(self):
        while not self._stop.wait(2.0):
            self._record_sample()

    def _record_sample(self, record=True):
        current = psutil.Process()
        children = current.children(recursive=True)
        webview_processes = [p for p in children if "msedgewebview2" in p.name().lower()]
        try:
            backend_rss = current.memory_info().rss
        except (psutil.Error, OSError):
            backend_rss = 0
        webview_rss = 0
        renderer_rss = 0
        gpu_rss = 0
        for process in webview_processes:
            try:
                memory = process.memory_info().rss
                command = " ".join(process.cmdline()).lower()
            except (psutil.Error, OSError):
                continue
            webview_rss += memory
            if "--type=renderer" in command:
                renderer_rss += memory
            elif "--type=gpu-process" in command:
                gpu_rss += memory

        tracker = self.api._tracker
        dispatcher = getattr(tracker, "_biome_transition_dispatcher", None) if tracker else None
        bridge = self.api._ui_bridge.snapshot()
        sample = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "backend_rss": backend_rss,
            "webview_rss": webview_rss,
            "renderer_rss": renderer_rss,
            "gpu_rss": gpu_rss,
            "webview_processes": len(webview_processes),
            "threads": threading.active_count(),
            "transition_queue": dispatcher.pending_count if dispatcher else 0,
            "frontend_pending": bridge["pending"],
            "frontend_blocked_for": bridge["blocked_for"],
        }
        with self._lock:
            self._latest_sample = sample
            if record and self._recording:
                self._samples.append(sample)
        return sample

    def record_pipeline(self, event, state, detail=""):
        with self._lock:
            self._pipeline.append({
                "timestamp": datetime.now().isoformat(timespec="milliseconds"),
                "event": str(event),
                "state": str(state),
                "detail": str(detail),
            })

    @staticmethod
    def _rpc_line(biome):
        return f'[BloxstrapRPC] {{"largeImage":{{"hoverText":"{biome}"}}}}'

    def _default_replay_lines(self, count):
        sequence = ["NORMAL", "WINDY", "NORMAL", "GLITCHED", "NORMAL", "CYBERSPACE", "NORMAL"]
        return [self._rpc_line(sequence[index % len(sequence)]) for index in range(max(1, count))]

    def _sanitize_replay_lines(self, lines, count):
        tracker = self.api._tracker
        if isinstance(lines, str):
            lines = lines.splitlines()
        elif not isinstance(lines, (list, tuple)):
            lines = []
        sanitized = [str(line) for line in lines if tracker._extract_biome_from_rpc_line(str(line))]
        return sanitized or self._default_replay_lines(count)

    def _fixture_screenshot(self, destination):
        from PIL import Image

        root = Path(os.environ["REOTEAB_RUNTIME_ROOT"]) / "diagnostics"
        root.mkdir(parents=True, exist_ok=True)
        fixture = root / "screenshot-fixture.png"
        if not fixture.exists():
            image = Image.new("RGB", (32, 32), "#16334a")
            try:
                image.save(fixture)
            finally:
                image.close()
        shutil.copy2(fixture, destination)
        return destination

    def _mock_requests_post(self, *args, **kwargs):
        has_attachment = bool(kwargs.get("files"))
        with self._lock:
            if has_attachment:
                self._replay["attachments"] += 1
        self.record_pipeline("webhook", f"mock {self._mock_webhook_mode}", "attachment" if has_attachment else "embed")
        if self._mock_webhook_mode == "timeout":
            time.sleep(0.2)
            import requests
            raise requests.exceptions.Timeout("DevLab simulated webhook timeout")
        if self._mock_webhook_mode == "failure":
            import requests
            raise requests.exceptions.ConnectionError("DevLab simulated webhook failure")

        class Response:
            status_code = 204

            @staticmethod
            def raise_for_status():
                return None

        return Response()

    def start_replay(self, lines=None, count=250, interval=0.05):
        tracker = self.api._tracker
        if tracker is None:
            return {"success": False, "error": "Tracker is not ready"}
        if self._replay_thread and self._replay_thread.is_alive():
            return {"success": False, "error": "A replay is already running"}
        try:
            count = max(1, min(int(count), 5000))
            interval = max(0.0, min(float(interval), 5.0))
        except (TypeError, ValueError):
            count, interval = 250, 0.05
        replay_lines = self._sanitize_replay_lines(lines, count)
        self._replay_stop.clear()
        with self._lock:
            self._replay = {"active": True, "events": len(replay_lines), "transitions": 0, "attachments": 0, "failed": 0}
        self._replay_thread = threading.Thread(
            target=self._run_replay,
            args=(replay_lines, interval),
            name="DevLab Log Replay",
            daemon=True,
        )
        self._replay_thread.start()
        return self.snapshot()

    def stop_replay(self):
        self._replay_stop.set()
        return self.snapshot()

    def _run_replay(self, lines, interval):
        import biome_tracker.mixin_webhook as webhook_module
        from biome_tracker.biome_transitions import BiomeTransitionDispatcher

        tracker = self.api._tracker
        with self._replay_lock:
            original = {
                "config": tracker.config,
                "current_biome": tracker.current_biome,
                "detection_running": tracker.detection_running,
                "generation": getattr(tracker, "_detection_generation", 0),
                "dispatcher": getattr(tracker, "_biome_transition_dispatcher", None),
                "get_latest_log_file": tracker.get_latest_log_file,
                "read_log_file": tracker.read_log_file,
                "send_screenshot": tracker._take_rare_biome_screenshot,
                "focus": tracker.is_roblox_focused,
                "activate": tracker.activate_roblox_window,
                "confirm": tracker.confirm_biome_popup,
                "post": webhook_module.requests.post,
                "webhook_urls": list(getattr(tracker, "webhook_urls", [])),
            }
            generation = max(1, original["generation"] + 1)
            replay_log = []
            config = dict(tracker.config or {})
            config["webhook_url"] = ["https://devlab.invalid/mock"]
            config["private_server_link"] = ""
            config["rare_biome_screenshot"] = True
            config["screenshot"] = False
            config["biome_notifier"] = {name: "Message" for name in tracker.biome_data}
            tracker.config = config
            tracker.webhook_urls = ["https://devlab.invalid/mock"]
            tracker.current_biome = "NORMAL"
            tracker.detection_running = True
            tracker._detection_generation = generation
            dispatcher = BiomeTransitionDispatcher(
                generation,
                tracker._is_detection_session_active,
                on_error=lambda error: self.record_pipeline("replay", "failed", str(error)),
            )
            tracker._biome_transition_dispatcher = dispatcher
            tracker.get_latest_log_file = lambda: "devlab-sanitized.log"
            tracker.read_log_file = lambda _path: list(replay_log)
            tracker._take_rare_biome_screenshot = self._fixture_screenshot
            tracker.is_roblox_focused = lambda: True
            tracker.activate_roblox_window = lambda: None
            tracker.confirm_biome_popup = lambda *args, **kwargs: True
            webhook_module.requests.post = self._mock_requests_post
            self.record_pipeline("replay", "started", f"{len(lines)} sanitized BloxstrapRPC lines")
            try:
                for index, line in enumerate(lines, start=1):
                    if self._replay_stop.is_set():
                        self.record_pipeline("replay", "stopped", f"after {index - 1} lines")
                        break
                    replay_log.append(line)
                    tracker.check_biome_in_logs()
                    dispatcher.wait_for_idle()
                    self.api._emit_macro_status()
                    self.api._emit_config_update()
                    if index % 12 == 0:
                        fixture = self._fixture_screenshot(
                            str(Path(os.environ["REOTEAB_RUNTIME_ROOT"]) / "diagnostics" / f"periodic-{index}.png")
                        )
                        tracker.send_aura_screenshot_webhook(fixture)
                        tracker.send_webhook_status("DevLab periodic status", color=0x16334A)
                    with self._lock:
                        self._replay["transitions"] = index
                    if self._replay_stop.wait(interval):
                        self.record_pipeline("replay", "stopped", f"after {index} lines")
                        break
                else:
                    self.record_pipeline("replay", "complete", f"{len(lines)} lines")
            except Exception as exc:
                with self._lock:
                    self._replay["failed"] += 1
                self.record_pipeline("replay", "failed", str(exc))
            finally:
                dispatcher.stop()
                tracker.config = original["config"]
                tracker.webhook_urls = original["webhook_urls"]
                tracker.current_biome = original["current_biome"]
                tracker.detection_running = original["detection_running"]
                tracker._detection_generation = original["generation"]
                tracker._biome_transition_dispatcher = original["dispatcher"]
                tracker.get_latest_log_file = original["get_latest_log_file"]
                tracker.read_log_file = original["read_log_file"]
                tracker._take_rare_biome_screenshot = original["send_screenshot"]
                tracker.is_roblox_focused = original["focus"]
                tracker.activate_roblox_window = original["activate"]
                tracker.confirm_biome_popup = original["confirm"]
                webhook_module.requests.post = original["post"]
                with self._lock:
                    self._replay["active"] = False

    def simulate_biome(self, biome, previous="NORMAL"):
        from biome_tracker.biome_transitions import BiomeTransitionDispatcher

        tracker = self.api._tracker
        if tracker is None:
            return {"success": False, "error": "Tracker is not ready"}
        biome = str(biome or "NORMAL").upper()
        previous = str(previous or "NORMAL").upper()
        self.record_pipeline(f"{previous}->{biome}", "queued")
        tracker.current_biome = previous
        tracker.detection_running = True
        tracker._detection_generation = max(1, getattr(tracker, "_detection_generation", 0) + 1)
        generation = tracker._detection_generation
        tracker.config = dict(tracker.config or {})
        tracker.config["webhook_url"] = []
        tracker.config["screenshot"] = False
        tracker.config["rare_biome_screenshot"] = False
        tracker.config["biome_notifier"] = {name: "None" for name in tracker.biome_data}

        dispatcher = BiomeTransitionDispatcher(
            generation,
            tracker._is_detection_session_active,
            on_error=lambda error: self.record_pipeline(f"{previous}->{biome}", "failed", str(error)),
        )
        tracker._biome_transition_dispatcher = dispatcher

        original_send = tracker.send_webhook
        original_focus = tracker.is_roblox_focused
        original_confirm = tracker.confirm_biome_popup
        tracker.send_webhook = lambda *args, **kwargs: self._mock_webhook(args[0] if args else biome)
        tracker.is_roblox_focused = lambda: False
        tracker.confirm_biome_popup = lambda *args, **kwargs: True
        try:
            submitted = dispatcher.submit(
                tracker.handle_biome_detection,
                biome,
                previous,
                generation,
                critical=biome == "CYBERSPACE" or previous == "CYBERSPACE",
                label=f"DevLab {previous}->{biome}",
            )
            if not submitted:
                return {"success": False, "error": "DevLab transition queue rejected the event"}
            dispatcher.wait_for_idle()
            self.record_pipeline(f"{previous}->{biome}", "complete")
            return {"success": True, "generation": generation}
        except Exception as exc:
            self.record_pipeline(f"{previous}->{biome}", "failed", str(exc))
            return {"success": False, "error": str(exc)}
        finally:
            tracker.send_webhook = original_send
            tracker.is_roblox_focused = original_focus
            tracker.confirm_biome_popup = original_confirm
            tracker.detection_running = False
            dispatcher.stop()
            tracker._biome_transition_dispatcher = None

    def _mock_webhook(self, biome):
        self.record_pipeline(str(biome), f"mock webhook {self._mock_webhook_mode}")
        if self._mock_webhook_mode == "timeout":
            time.sleep(0.2)
            raise TimeoutError("DevLab simulated webhook timeout")
        if self._mock_webhook_mode == "failure":
            raise RuntimeError("DevLab simulated webhook failure")
        return True

    def start_stress(self, rate=20):
        self.stop_stress()
        self._stress_stop.clear()
        rate = max(1, min(int(rate), 200))

        def run():
            delay = 1.0 / rate
            index = 0
            while not self._stress_stop.wait(delay):
                index += 1
                self.api._safe_eval_js("devlab-status", f"if(window.onDevLabStatus) window.onDevLabStatus({json.dumps(index)});")

        self._stress_thread = threading.Thread(target=run, name="DevLab WebView Stress", daemon=True)
        self._stress_thread.start()
        return self.snapshot()

    def stop_stress(self):
        self._stress_stop.set()
        return self.snapshot()

    def set_webhook_mode(self, mode):
        if mode in {"success", "timeout", "failure"}:
            self._mock_webhook_mode = mode
        return self.snapshot()

    def simulate_screenshot_webhook(self):
        return self.start_replay([self._rpc_line("CYBERSPACE")], count=1, interval=0)

    def set_fault(self, fault):
        self._fault = fault if fault in {"bridge-stall", "drop-ui", None, ""} else None
        self.api._ui_bridge.set_fault(self._fault)
        self.record_pipeline("fault", "changed", self._fault or "none")
        return self.snapshot()

    def capture_thread_stacks(self):
        frames = sys._current_frames()
        relevant = {"Biome Transitions", "WebView Bridge", "DevLab Log Replay", "DevLab WebView Stress"}
        stacks = []
        for thread in threading.enumerate():
            if thread.name not in relevant or thread.ident not in frames:
                continue
            summary = traceback.extract_stack(frames[thread.ident])[-8:]
            stacks.append({
                "thread": thread.name,
                "frames": [f"{Path(frame.filename).name}:{frame.lineno} in {frame.name}" for frame in summary],
            })
        with self._lock:
            self._thread_stacks = stacks
        self.record_pipeline("threads", "captured", f"{len(stacks)} relevant stacks")
        return self.snapshot()

    def export_report(self):
        root = Path(os.environ["REOTEAB_RUNTIME_ROOT"]) / "diagnostics"
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        csv_path = root / f"devlab-{stamp}.csv"
        report_path = root / f"devlab-{stamp}.json"
        with self._lock:
            samples = list(self._samples)
            pipeline = list(self._pipeline)
        if samples:
            with csv_path.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=list(samples[0]))
                writer.writeheader()
                writer.writerows(samples)
        report_path.write_text(json.dumps({
            "build": "Reoteab DevLab",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "sample_count": len(samples),
            "duration_seconds": self._sample_duration(samples),
            "bridge": self.api._ui_bridge.snapshot(),
            "ui_maintenance": self.api._ui_maintenance.snapshot(),
            "samples": samples,
            "pipeline": pipeline,
            "replay": self._replay,
            "thread_stacks": self._thread_stacks,
        }, indent=2), encoding="utf-8")
        return {"success": True, "csv": str(csv_path) if samples else None, "report": str(report_path)}

    @staticmethod
    def _sample_duration(samples):
        if len(samples) < 2:
            return 0.0
        try:
            first = datetime.fromisoformat(samples[0]["timestamp"])
            last = datetime.fromisoformat(samples[-1]["timestamp"])
            return round((last - first).total_seconds(), 3)
        except (KeyError, TypeError, ValueError):
            return 0.0

    def snapshot(self):
        latest_sample = self._record_sample(record=False)
        tracker = self.api._tracker
        dispatcher = getattr(tracker, "_biome_transition_dispatcher", None) if tracker else None
        with self._lock:
            samples = list(self._samples)
            pipeline = list(self._pipeline)
        return {
            "recording": self._recording,
            "latest": latest_sample,
            "samples": samples[-180:],
            "pipeline": pipeline[-80:],
            "bridge": self.api._ui_bridge.snapshot(),
            "transition_queue": dispatcher.pending_count if dispatcher else 0,
            "worker_health": getattr(tracker, "_detection_worker_health", {}) if tracker else {},
            "webhook_mode": self._mock_webhook_mode,
            "fault": self._fault,
            "replay": self._replay,
            "thread_stacks": self._thread_stacks,
            "ui_maintenance": self.api._ui_maintenance.snapshot(),
        }
