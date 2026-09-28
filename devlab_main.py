from __future__ import annotations

import os
from pathlib import Path

os.environ["REOTEAB_DEVLAB"] = "1"
os.environ.setdefault(
    "REOTEAB_RUNTIME_ROOT",
    str(Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Reoteab-DevLab"),
)

from devlab import DevLabDiagnostics
from main import Api, main


class DevLabApi(Api):
    def __init__(self, tracker=None):
        super().__init__(tracker)
        self._devlab = DevLabDiagnostics(self)

    def on_tracker_ready(self, tracker):
        tracker.config = dict(tracker.config or {})
        tracker.config["webhook_url"] = []

    def _setup_emergency_server(self):
        return None

    def _setup_emergency_hotkey(self):
        return None

    def set_biome_detection(self, enabled):
        if enabled:
            self._devlab.record_pipeline("macro", "blocked", "DevLab does not start Roblox automation")
            return
        super().set_biome_detection(False)

    def save_config(self, config_data):
        config_data = dict(config_data or {})
        config_data["webhook_url"] = []
        config_data["private_server_link"] = ""
        return super().save_config(config_data)

    def get_devlab_snapshot(self):
        return self._devlab.snapshot()

    def start_devlab_recording(self):
        return self._devlab.start_recording()

    def stop_devlab_recording(self):
        return self._devlab.stop_recording()

    def export_devlab_report(self):
        return self._devlab.export_report()

    def simulate_devlab_biome(self, biome, previous="NORMAL"):
        return self._devlab.simulate_biome(biome, previous)

    def start_devlab_stress(self, rate=20):
        return self._devlab.start_stress(rate)

    def stop_devlab_stress(self):
        return self._devlab.stop_stress()

    def start_devlab_replay(self, lines=None, count=250, interval=0.05):
        return self._devlab.start_replay(lines, count, interval)

    def stop_devlab_replay(self):
        return self._devlab.stop_replay()

    def set_devlab_webhook_mode(self, mode):
        return self._devlab.set_webhook_mode(mode)

    def simulate_devlab_screenshot_webhook(self):
        return self._devlab.simulate_screenshot_webhook()

    def set_devlab_fault(self, fault=None):
        return self._devlab.set_fault(fault)

    def capture_devlab_thread_stacks(self):
        return self._devlab.capture_thread_stacks()


if __name__ == "__main__":
    raise SystemExit(main(api_class=DevLabApi))
