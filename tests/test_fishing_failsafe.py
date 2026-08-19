import threading
import unittest
from unittest import mock

from biome_tracker import fishing
from biome_tracker.fishing_failsafe import FishingFailsafeTimer


class FakeClock:
    def __init__(self, now=0.0):
        self.now = float(now)

    def monotonic(self):
        return self.now

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += max(0.0, float(seconds))


class FishingFailsafeTimerTests(unittest.TestCase):
    def test_normal_fishing_timeout_still_triggers(self):
        timer = FishingFailsafeTimer(60)
        timer.start(10)
        self.assertFalse(timer.expired(69.9))
        self.assertTrue(timer.expired(70))

    def test_short_merchant_sequence_does_not_trigger_failsafe(self):
        timer = FishingFailsafeTimer(60)
        timer.start(0)
        timer.pause(50)
        self.assertFalse(timer.expired(55))
        timer.resume(55)
        self.assertFalse(timer.expired(60))

    def test_long_merchant_sequence_does_not_trigger_while_active(self):
        timer = FishingFailsafeTimer(60)
        timer.start(0)
        timer.pause(20)
        self.assertFalse(timer.expired(100))
        self.assertEqual(timer.elapsed(100), 20)

    def test_failsafe_resumes_after_merchant_sequence_completes(self):
        timer = FishingFailsafeTimer(60)
        timer.start(0)
        timer.pause(20)
        timer.resume(100)
        self.assertFalse(timer.expired(139.9))
        self.assertTrue(timer.expired(140))

    def test_failsafe_resumes_after_merchant_sequence_errors(self):
        timer = FishingFailsafeTimer(60)
        timer.start(0)
        timer.pause(20)
        try:
            raise RuntimeError("merchant failed")
        except RuntimeError:
            pass
        finally:
            timer.resume(100)
        self.assertFalse(timer.expired(139.9))
        self.assertTrue(timer.expired(140))


class FishingMerchantFlowRegressionTests(unittest.TestCase):
    def _run_top_level_flow(self, *, merchant_error=False, merchant_exception=None):
        clock = FakeClock()
        stop_event = threading.Event()
        runtime_state = {
            "fish_caught_count": 0,
            "fish_caught_since_merchant": 0,
            "fish_caught_since_br_sc": 0,
            "merchant_requires_reset": False,
            "merchant_sequence_active": False,
        }
        observations = {
            "merchant_entry_active": False,
            "restart_active": False,
            "restart_ignored": False,
            "merchant_started_at": None,
            "watchdog_started_at": None,
            "restart_at": None,
            "timeout_at": None,
            "raised": None,
        }
        phase = {"merchant_finished": False, "restart_seen": False}

        def is_failsafe_ignored():
            return bool(runtime_state["merchant_sequence_active"])

        class FakeAutoIt:
            @staticmethod
            def mouse_click(_button, x, y, *_args, **_kwargs):
                if (x, y) == (862, 843) and not phase["merchant_finished"]:
                    observations["watchdog_started_at"] = clock.now
                if phase["merchant_finished"] and not phase["restart_seen"]:
                    clock.now += 90
                    observations["restart_active"] = runtime_state["merchant_sequence_active"]
                    observations["restart_ignored"] = is_failsafe_ignored()
                    observations["restart_at"] = clock.now
                    phase["restart_seen"] = True

            @staticmethod
            def send(*args, **kwargs):
                return None

        def run_merchant_sequence():
            observations["merchant_entry_active"] = runtime_state["merchant_sequence_active"]
            observations["merchant_started_at"] = clock.now
            # Navigation and OCR exceed the production timeout before the inner
            # merchant interaction is considered complete.
            clock.now += 90
            phase["merchant_finished"] = True
            if merchant_exception is not None:
                raise merchant_exception
            if merchant_error:
                raise RuntimeError("merchant navigation failed")
            return False

        def on_failsafe_timeout():
            observations["timeout_at"] = clock.now
            stop_event.set()

        config = {
            "auto_reconnect": True,
            "fishing_failsafe_rejoin": True,
            "fishing_bugged_ui_rejoin_failsafe": False,
            "fishing_use_merchant_every_x_fish": True,
            "fishing_merchant_every_x_fish": 1,
            "fishing_actions_delay_ms": 0,
        }

        with (
            mock.patch.object(fishing, "time", clock),
            mock.patch.object(fishing, "autoit", FakeAutoIt),
            mock.patch.object(fishing, "mss", None),
            mock.patch.object(fishing, "_get_pixel_rgb", return_value=(0, 0, 0)),
            mock.patch.object(
                fishing,
                "is_indicator_active",
                side_effect=lambda _pixel: not phase["merchant_finished"],
            ),
            mock.patch.object(fishing, "detect_colour", return_value=True),
            mock.patch.object(fishing, "_run_pre_fishing_sequence", return_value=True),
            mock.patch.object(fishing, "_run_equip_aura_before_movement", return_value=True),
            mock.patch.object(fishing, "_run_walk_to_fish_path", return_value=True),
            mock.patch.object(fishing, "_autoit_key_up", return_value=None),
        ):
            try:
                fishing.run_fishing_loop(
                    stop_event=stop_event,
                    config_provider=lambda: config,
                    config_refresh_seconds=1000,
                    print_start_stop=False,
                    on_failsafe_timeout=on_failsafe_timeout,
                    run_merchant_sequence_cb=run_merchant_sequence,
                    runtime_state=runtime_state,
                    is_failsafe_ignored_cb=is_failsafe_ignored,
                )
            except BaseException as exc:
                observations["raised"] = exc

        return observations, runtime_state

    def test_navigation_and_ocr_delay_are_guarded_until_fishing_restarts(self):
        observations, runtime_state = self._run_top_level_flow()

        self.assertTrue(observations["merchant_entry_active"])
        self.assertTrue(observations["restart_active"])
        self.assertTrue(observations["restart_ignored"])
        self.assertFalse(runtime_state["merchant_sequence_active"])

        resumed_for = observations["timeout_at"] - observations["restart_at"]
        elapsed_before_merchant = observations["merchant_started_at"] - observations["watchdog_started_at"]
        self.assertAlmostEqual(resumed_for, 60 - elapsed_before_merchant, places=2)

    def test_top_level_merchant_error_clears_guard_after_fishing_restarts(self):
        observations, runtime_state = self._run_top_level_flow(merchant_error=True)

        self.assertTrue(observations["merchant_entry_active"])
        self.assertTrue(observations["restart_active"])
        self.assertFalse(runtime_state["merchant_sequence_active"])
        self.assertIsNotNone(observations["timeout_at"])

    def test_unhandled_merchant_exception_clears_guard_in_finally(self):
        observations, runtime_state = self._run_top_level_flow(
            merchant_exception=KeyboardInterrupt()
        )

        self.assertTrue(observations["merchant_entry_active"])
        self.assertIsInstance(observations["raised"], KeyboardInterrupt)
        self.assertFalse(runtime_state["merchant_sequence_active"])


if __name__ == "__main__":
    unittest.main()
