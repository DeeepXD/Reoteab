from __future__ import annotations

import ctypes
import os
import threading
import time


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_SET_QUOTA = 0x0100


class RobloxMemoryTrimmer:
    def __init__(self, tracker, clock=time.monotonic, sleeper=time.sleep, empty_working_set=None):
        self.tracker = tracker
        self._clock = clock
        self._sleep = sleeper
        self._empty_working_set = empty_working_set or self._empty_working_set_native
        self._stop = threading.Event()
        self._thread = None
        self._trim_lock = threading.Lock()
        self._last_trim_at = self._clock()
        self._last_result = {"status": "not run"}
        self._recheck = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._last_trim_at = self._clock()
        self._thread = threading.Thread(target=self._run, name="Roblox Memory Trim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._recheck = None
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        if not thread or not thread.is_alive():
            self._thread = None

    def snapshot(self):
        result = dict(self._last_result)
        result["enabled"] = bool(self.tracker.config.get("roblox_memory_trim_enabled", False))
        result["worker_running"] = bool(self._thread and self._thread.is_alive())
        return result

    def request_manual_trim(self):
        if not self._trim_lock.acquire(blocking=False):
            return {"status": "busy", "message": "A Roblox memory trim is already running."}

        def run():
            try:
                self._trim_once(manual=True, lock_held=True)
            finally:
                self._trim_lock.release()

        threading.Thread(target=run, name="Roblox Memory Trim Now", daemon=True).start()
        return {"status": "queued", "message": "Roblox memory trim queued."}

    def _run(self):
        while not self._stop.wait(15.0):
            self._record_recheck()
            if not bool(self.tracker.config.get("roblox_memory_trim_enabled", False)):
                continue
            interval = self._interval_seconds()
            if self._clock() - self._last_trim_at < interval:
                continue
            if not self._trim_lock.acquire(blocking=False):
                continue
            try:
                self._trim_once(manual=False, lock_held=True)
            finally:
                self._trim_lock.release()

    def _interval_seconds(self):
        try:
            minutes = int(self.tracker.config.get("roblox_memory_trim_interval_minutes", 60))
        except (TypeError, ValueError):
            minutes = 60
        return max(15, min(minutes, 720)) * 60

    def _threshold_bytes(self):
        try:
            megabytes = int(self.tracker.config.get("roblox_memory_trim_threshold_mb", 2048))
        except (TypeError, ValueError):
            megabytes = 2048
        return max(512, min(megabytes, 8192)) * 1024 * 1024

    def _set_result(self, status, message, **details):
        result = {"status": status, "message": message, "timestamp": time.time()}
        result.update(details)
        self._last_result = result
        return dict(result)

    def _trim_once(self, manual=False, lock_held=False):
        if not lock_held and not self._trim_lock.acquire(blocking=False):
            return self._set_result("busy", "A Roblox memory trim is already running.")
        try:
            if not manual and not bool(self.tracker.config.get("roblox_memory_trim_enabled", False)):
                return self._set_result("disabled", "Automatic Roblox memory trimming is disabled.")
            if not bool(getattr(self.tracker, "detection_running", False)):
                return self._set_result("skipped", "Macro is not running.")
            if bool(getattr(self.tracker, "reconnecting_state", False)):
                return self._set_result("skipped", "Roblox is reconnecting.")

            process = self.tracker.get_active_roblox_process()
            if process is None:
                return self._set_result("skipped", "Active Roblox window was not found.")

            try:
                before = int(process.memory_info().rss)
            except Exception:
                return self._set_result("skipped", "Could not read Roblox memory.")

            if not manual and before < self._threshold_bytes():
                return self._set_result(
                    "below-threshold",
                    "Roblox memory is below the configured trim threshold.",
                    pid=process.pid,
                    before_rss=before,
                )

            try:
                self._empty_working_set(process.pid)
            except OSError as exc:
                return self._set_result("failed", "Windows could not trim Roblox memory.", pid=process.pid, error=exc.winerror or exc.errno)
            except Exception:
                return self._set_result("failed", "Windows could not trim Roblox memory.", pid=process.pid)

            self._sleep(0.35)
            try:
                after = int(process.memory_info().rss)
            except Exception:
                after = before
            reclaimed = max(0, before - after)
            self._last_trim_at = self._clock()
            self._recheck = {"pid": process.pid, "after_rss": after, "at": self._clock() + 30.0}
            self._append_log(f"[Memory Trim] Roblox working set: {before // (1024 * 1024)} MB -> {after // (1024 * 1024)} MB")
            return self._set_result(
                "trimmed",
                "Roblox working set trimmed.",
                pid=process.pid,
                before_rss=before,
                after_rss=after,
                reclaimed_rss=reclaimed,
                manual=bool(manual),
            )
        finally:
            if not lock_held:
                self._trim_lock.release()

    def _append_log(self, message):
        try:
            self.tracker.append_log(message)
        except Exception:
            pass

    def _record_recheck(self):
        recheck = self._recheck
        if not recheck or self._clock() < recheck["at"]:
            return
        self._recheck = None
        try:
            process = self.tracker.get_active_roblox_process()
            if process is None or process.pid != recheck["pid"]:
                return
            follow_up = int(process.memory_info().rss)
        except Exception:
            return
        result = dict(self._last_result)
        if result.get("pid") != recheck["pid"]:
            return
        result["follow_up_rss"] = follow_up
        result["returned_rss"] = max(0, follow_up - recheck["after_rss"])
        self._last_result = result

    @staticmethod
    def _empty_working_set_native(pid):
        if os.name != "nt":
            raise OSError("Roblox memory trimming is only available on Windows.")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_bool
        psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
        psapi.EmptyWorkingSet.restype = ctypes.c_bool

        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_SET_QUOTA, False, int(pid))
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not psapi.EmptyWorkingSet(handle):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            kernel32.CloseHandle(handle)
