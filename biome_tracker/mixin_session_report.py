from collections import Counter
from datetime import datetime
import threading
import time

from .base_support import rare_biomes


class SessionReportMixin:
    def _initialize_macro_report(self):
        self._macro_report_lock = threading.Lock()
        self._macro_report = None

    def start_macro_report(self, started_at=None):
        report_started_at = started_at or datetime.now()
        with self._macro_report_lock:
            self._macro_report = {
                "started_at": report_started_at,
                "started_monotonic": time.monotonic(),
                "sent": False,
                "biome_transitions": 0,
                "rare_biomes": Counter(),
                "merchants": Counter(),
                "reconnect_attempts": 0,
                "reconnect_recoveries": 0,
                "reconnect_pending": False,
                "failsafes": Counter(),
            }

    def record_macro_report_biome(self, biome):
        biome_name = str(biome or "").upper().strip()
        if not biome_name or biome_name == "NORMAL":
            return
        with self._macro_report_lock:
            report = self._macro_report
            if not report or report["sent"]:
                return
            report["biome_transitions"] += 1
            if biome_name in rare_biomes:
                report["rare_biomes"][biome_name] += 1

    def record_macro_report_merchant(self, merchant_name):
        name = str(merchant_name or "").strip()
        if not name:
            return
        with self._macro_report_lock:
            report = self._macro_report
            if report and not report["sent"]:
                report["merchants"][name] += 1

    def record_macro_report_reconnect_attempt(self):
        with self._macro_report_lock:
            report = self._macro_report
            if not report or report["sent"] or report["reconnect_pending"]:
                return
            report["reconnect_attempts"] += 1
            report["reconnect_pending"] = True

    def record_macro_report_reconnect_recovery(self):
        with self._macro_report_lock:
            report = self._macro_report
            if not report or report["sent"] or not report["reconnect_pending"]:
                return
            report["reconnect_recoveries"] += 1
            report["reconnect_pending"] = False

    def record_macro_report_failsafe(self, name):
        label = str(name or "").strip()
        if not label:
            return
        with self._macro_report_lock:
            report = self._macro_report
            if report and not report["sent"]:
                report["failsafes"][label] += 1

    def finish_macro_report(self, ended_at=None):
        with self._macro_report_lock:
            report = self._macro_report
            if not report or report["sent"]:
                return None
            report["sent"] = True
            return {
                "started_at": report["started_at"],
                "ended_at": ended_at or datetime.now(),
                "duration_seconds": max(0, int(time.monotonic() - report["started_monotonic"])),
                "biome_transitions": report["biome_transitions"],
                "rare_biomes": dict(report["rare_biomes"]),
                "merchants": dict(report["merchants"]),
                "reconnect_attempts": report["reconnect_attempts"],
                "reconnect_recoveries": report["reconnect_recoveries"],
                "failsafes": dict(report["failsafes"]),
            }
