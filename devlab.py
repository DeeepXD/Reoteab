from __future__ import annotations

import csv
import json
import os
import threading
import time
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
        self._mock_webhook_mode = "success"
        self._fault = None

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
        from PIL import Image

        root = Path(os.environ["REOTEAB_RUNTIME_ROOT"]) / "diagnostics"
        root.mkdir(parents=True, exist_ok=True)
        fixture = root / "screenshot-fixture.png"
        image = Image.new("RGB", (8, 8), "#16334a")
        try:
            image.save(fixture)
        finally:
            image.close()
        self.record_pipeline("screenshot", "fixture captured", fixture.name)
        try:
            self._mock_webhook("CYBERSPACE")
        except Exception as exc:
            self.record_pipeline("screenshot", "mock delivery failed", str(exc))
            return {"success": False, "error": str(exc)}
        self.record_pipeline("screenshot", "mock delivery complete")
        return {"success": True, "fixture": str(fixture)}

    def set_fault(self, fault):
        self._fault = fault if fault in {"bridge-stall", "drop-ui", None, ""} else None
        self.api._ui_bridge.set_fault(self._fault)
        self.record_pipeline("fault", "changed", self._fault or "none")
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
            "samples": samples,
            "pipeline": pipeline,
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
        }
