from __future__ import annotations

import os
import threading
import time
from collections import deque

import psutil


class UiMaintenanceManager:
    """Monitors WebView memory and records safe maintenance opportunities."""

    def __init__(self, api, sample_interval=60.0, foreground_idle=600.0,
                 background_idle=120.0, scheduled_interval=5400.0,
                 cooldown=900.0, clock=time.monotonic, process_factory=psutil.Process):
        self.api = api
        self.sample_interval = self._env_seconds("REOTEAB_UI_SAMPLE_SECONDS", sample_interval)
        self.foreground_idle = self._env_seconds("REOTEAB_UI_FOREGROUND_IDLE_SECONDS", foreground_idle)
        self.background_idle = self._env_seconds("REOTEAB_UI_BACKGROUND_IDLE_SECONDS", background_idle)
        self.scheduled_interval = self._env_seconds("REOTEAB_UI_SCHEDULE_SECONDS", scheduled_interval)
        self.cooldown = self._env_seconds("REOTEAB_UI_COOLDOWN_SECONDS", cooldown)
        self.renderer_limit = self._env_megabytes("REOTEAB_UI_RENDERER_LIMIT_MB", 650)
        self.total_limit = self._env_megabytes("REOTEAB_UI_TOTAL_LIMIT_MB", 900)
        self._clock = clock
        self._process_factory = process_factory
        self._lock = threading.Lock()
        self._maintenance_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._window = None
        self._samples = deque(maxlen=6)
        now = self._clock()
        self._last_interaction = now
        self._last_maintenance = now
        self._pending_reason = None
        self._last_deferred_reason = None
        self._ui_state = {
            "active_page": "notice",
            "theme": "midnight",
            "scroll_y": 0,
            "editing": False,
            "dirty": False,
            "modal": False,
            "calibration": False,
            "file_dialog": False,
            "saving": False,
        }
        self._last_result = {"status": "not requested"}
        self._renderer_failed = False

    @staticmethod
    def _env_megabytes(name, default):
        try:
            return max(1, int(os.environ.get(name, default))) * 1024 * 1024
        except (TypeError, ValueError):
            return default * 1024 * 1024

    @staticmethod
    def _env_seconds(name, default):
        try:
            return max(1.0, float(os.environ.get(name, default)))
        except (TypeError, ValueError):
            return max(1.0, float(default))

    def set_window(self, window):
        with self._lock:
            self._window = window
        self._attach_renderer_failure_handler(window)
        if self._thread is None:
            self._thread = threading.Thread(target=self._monitor_loop, name="WebView Maintenance", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()

    def report_ui_state(self, state):
        if not isinstance(state, dict):
            return self.snapshot()
        now = self._clock()
        with self._lock:
            for key in self._ui_state:
                if key not in state:
                    continue
                if key == "scroll_y":
                    try:
                        self._ui_state[key] = max(0, int(state[key]))
                    except (TypeError, ValueError):
                        pass
                elif key in ("active_page", "theme"):
                    value = str(state[key] or "").strip()
                    if value:
                        self._ui_state[key] = value[:80]
                else:
                    self._ui_state[key] = bool(state[key])
            if state.get("interaction"):
                self._last_interaction = now
                self._pending_reason = None
        return self.snapshot()

    def set_operation(self, name, active):
        if name not in ("calibration", "file_dialog", "saving"):
            return
        with self._lock:
            self._ui_state[name] = bool(active)
            if active:
                self._last_interaction = self._clock()
                self._pending_reason = None

    def request_renderer_recovery(self, detail="renderer failure"):
        with self._lock:
            self._renderer_failed = True
            self._pending_reason = detail
        return self.snapshot()

    def snapshot(self):
        with self._lock:
            sample = dict(self._samples[-1]) if self._samples else self._memory_sample()
            state = dict(self._ui_state)
            state.update({
                "pending_reason": self._pending_reason,
                "last_deferred_reason": self._last_deferred_reason,
                "seconds_since_interaction": round(max(0.0, self._clock() - self._last_interaction), 1),
                "last_result": dict(self._last_result),
                "renderer_failed": self._renderer_failed,
            })
            return {"memory": sample, "ui": state}

    def run_once(self):
        sample = self._memory_sample()
        now = self._clock()
        with self._lock:
            self._samples.append(sample)
            reason = self._pending_reason or self._maintenance_reason_locked(now)
            if reason:
                self._pending_reason = reason
        if not reason:
            return {"status": "healthy", "memory": sample}

        allowed, deferred = self._can_maintain(now)
        if not allowed:
            with self._lock:
                self._last_deferred_reason = deferred
            return {"status": "deferred", "reason": deferred, "memory": sample}
        return self._refresh(reason, sample)

    def _monitor_loop(self):
        while not self._stop.wait(self.sample_interval):
            try:
                self.run_once()
            except Exception:
                pass

    def _memory_sample(self):
        try:
            current = self._process_factory()
            children = current.children(recursive=True)
        except (psutil.Error, OSError):
            return {"total": 0, "renderer": 0, "processes": 0}

        total = renderer = 0
        processes = 0
        for process in children:
            try:
                if "msedgewebview2" not in process.name().lower():
                    continue
                memory = process.memory_info().rss
                command = " ".join(process.cmdline()).lower()
            except (psutil.Error, OSError):
                continue
            processes += 1
            total += memory
            if "--type=renderer" in command:
                renderer += memory
        return {"total": total, "renderer": renderer, "processes": processes}

    def _maintenance_reason_locked(self, now):
        if now - self._last_maintenance < self.cooldown:
            return None
        if self._renderer_failed:
            return "renderer recovery"
        if now - self._last_maintenance >= self.scheduled_interval:
            return "scheduled maintenance"
        if len(self._samples) < 4:
            return None
        recent = list(self._samples)[-4:]
        growing = all(recent[index]["total"] <= recent[index + 1]["total"] for index in range(3))
        total_growth = recent[-1]["total"] - recent[0]["total"]
        renderer_growth = recent[-1]["renderer"] - recent[0]["renderer"]
        current = recent[-1]
        if current["renderer"] >= self.renderer_limit and growing and renderer_growth >= 80 * 1024 * 1024:
            return "sustained renderer growth"
        if current["total"] >= self.total_limit and growing and total_growth >= 120 * 1024 * 1024:
            return "sustained WebView growth"
        return None

    def _window_state(self):
        with self._lock:
            window = self._window
        if window is None:
            return False, False
        try:
            import win32gui

            native = getattr(window, "native", None)
            hwnd = getattr(getattr(window, "gui", None), "hwnd", None)
            if not hwnd and native is not None:
                handle = getattr(native, "Handle", None)
                if handle is not None:
                    hwnd = int(handle.ToInt32())
            if not hwnd:
                hwnd = win32gui.FindWindow(None, window.title)
            if not hwnd:
                return False, False
            return win32gui.GetForegroundWindow() == hwnd, bool(win32gui.IsIconic(hwnd))
        except Exception:
            return False, False

    def _can_maintain(self, now):
        foreground, minimized = self._window_state()
        with self._lock:
            state = dict(self._ui_state)
            idle_for = now - self._last_interaction
        for key, label in (("dirty", "unsaved changes"), ("editing", "active edit"),
                           ("modal", "open dialog"), ("calibration", "calibration"),
                           ("file_dialog", "file dialog"), ("saving", "save operation")):
            if state[key]:
                return False, label
        if foreground and idle_for < self.foreground_idle:
            return False, "foreground activity"
        if not foreground and idle_for < self.background_idle:
            return False, "background activity"
        if minimized and idle_for < self.background_idle:
            return False, "minimized activity"
        return True, None

    def _refresh(self, reason, before):
        if not self._maintenance_lock.acquire(blocking=False):
            return {"status": "already running"}
        try:
            now = self._clock()
            allowed, deferred = self._can_maintain(now)
            if not allowed:
                with self._lock:
                    self._last_deferred_reason = deferred
                return {"status": "deferred", "reason": deferred}
            with self._lock:
                window = self._window
            if window is None:
                return {"status": "unavailable"}
            result = {
                "status": "deferred",
                "reason": reason,
                "error": "Automatic WebView reload is unavailable in this pywebview runtime",
                "before": before,
            }
            with self._lock:
                self._last_maintenance = self._clock()
                self._last_deferred_reason = "safe renderer reload unavailable"
                self._last_result = result
            return result
        finally:
            self._maintenance_lock.release()

    def _attach_renderer_failure_handler(self, window):
        try:
            native = getattr(window, "native", None)
            gui = getattr(window, "gui", None)
            browser = getattr(native, "browser", None)
            candidates = (
                getattr(browser, "webview", None),
                getattr(native, "webview", None),
                getattr(gui, "webview", None),
                native,
                gui,
            )
            for candidate in candidates:
                core = getattr(candidate, "CoreWebView2", None)
                failed = getattr(core, "ProcessFailed", None) if core is not None else None
                if failed is not None:
                    failed += self._on_renderer_failure
                    return
        except Exception:
            pass

    def _on_renderer_failure(self, *_args):
        self.request_renderer_recovery()
