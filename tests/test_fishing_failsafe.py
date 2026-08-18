import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "biome_tracker" / "fishing_failsafe.py"
SPEC = importlib.util.spec_from_file_location("fishing_failsafe", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
FishingFailsafeTimer = MODULE.FishingFailsafeTimer


class FakeClock:
    def __init__(self, now=0.0):
        self.now = float(now)

    def monotonic(self):
        return self.now


class FishingFailsafeTimerTests(unittest.TestCase):
    def test_normal_fishing_timeout_still_triggers(self):
        timer = FishingFailsafeTimer(60)
        timer.start(10)
        self.assertFalse(timer.expired(69.9))
        self.assertTrue(timer.expired(70))

    def test_short_merchant_sequence_does_not_trigger_failsafe(self):
        clock = FakeClock(0)
        timer = FishingFailsafeTimer(60)
        timer.start(clock.monotonic())
        clock.now = 50

        def merchant():
            clock.now = 55

        timer.run_paused(merchant, clock.monotonic)
        self.assertFalse(timer.expired(60))

    def test_long_merchant_sequence_does_not_trigger_while_active(self):
        clock = FakeClock(0)
        timer = FishingFailsafeTimer(60)
        timer.start(clock.monotonic())
        clock.now = 20
        state = {"merchant_sequence_active": False}

        def merchant():
            clock.now = 100
            self.assertTrue(state["merchant_sequence_active"])
            self.assertFalse(timer.expired(clock.monotonic()))

        timer.run_paused(
            merchant,
            clock.monotonic,
            lambda active: state.update(merchant_sequence_active=active),
        )
        self.assertFalse(state["merchant_sequence_active"])
        self.assertFalse(timer.expired(clock.monotonic()))

    def test_failsafe_resumes_after_merchant_sequence_completes(self):
        clock = FakeClock(0)
        timer = FishingFailsafeTimer(60)
        timer.start(clock.monotonic())
        clock.now = 20

        def merchant():
            clock.now = 100

        timer.run_paused(merchant, clock.monotonic)
        self.assertFalse(timer.expired(139.9))
        self.assertTrue(timer.expired(140))

    def test_failsafe_resumes_after_merchant_sequence_errors(self):
        clock = FakeClock(0)
        timer = FishingFailsafeTimer(60)
        timer.start(clock.monotonic())
        clock.now = 20
        state = {"merchant_sequence_active": False}

        def merchant():
            clock.now = 100
            raise RuntimeError("merchant failed")

        with self.assertRaisesRegex(RuntimeError, "merchant failed"):
            timer.run_paused(
                merchant,
                clock.monotonic,
                lambda active: state.update(merchant_sequence_active=active),
            )

        self.assertFalse(state["merchant_sequence_active"])
        self.assertFalse(timer.expired(139.9))
        self.assertTrue(timer.expired(140))


if __name__ == "__main__":
    unittest.main()
