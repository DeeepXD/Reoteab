import importlib.util
import threading
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "biome_tracker" / "biome_transitions.py"
SPEC = importlib.util.spec_from_file_location("biome_transitions", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
BiomeTransitionDispatcher = MODULE.BiomeTransitionDispatcher
biome_webhook_events = MODULE.biome_webhook_events


class TransitionHarness:
    def __init__(self, sender=None):
        self.current_biome = "NORMAL"
        self.events = []
        self.errors = []
        self.sender = sender or self.events.append
        self.dispatcher = BiomeTransitionDispatcher(self.errors.append)

    def detect(self, biome):
        if biome == self.current_biome:
            return
        previous_biome = self.current_biome
        self.current_biome = biome
        self.dispatcher.submit(self._deliver, previous_biome, biome)

    def _deliver(self, previous_biome, biome):
        for event in biome_webhook_events(previous_biome, biome):
            self.sender(event)

    def wait(self):
        self.dispatcher.wait_for_idle()


class BiomeTransitionTests(unittest.TestCase):
    def test_start_event_emitted_once(self):
        harness = TransitionHarness()
        harness.detect("WINDY")
        harness.wait()
        self.assertEqual(harness.events, [("WINDY", "start")])

    def test_end_event_emitted_once(self):
        harness = TransitionHarness()
        harness.detect("WINDY")
        harness.wait()
        harness.events.clear()
        harness.detect("NORMAL")
        harness.wait()
        self.assertEqual(harness.events, [("WINDY", "end")])

    def test_repeated_same_biome_or_log_rotation_does_not_duplicate(self):
        harness = TransitionHarness()
        harness.detect("WINDY")
        harness.detect("WINDY")
        harness.detect("WINDY")
        harness.wait()
        self.assertEqual(harness.events, [("WINDY", "start")])

    def test_a_to_b_emits_end_then_start_in_order(self):
        first_start_entered = threading.Event()
        release_first_start = threading.Event()
        delivered = []

        def delayed_sender(event):
            if event == ("WINDY", "start"):
                first_start_entered.set()
                release_first_start.wait(1)
            delivered.append(event)

        harness = TransitionHarness(delayed_sender)
        harness.detect("WINDY")
        self.assertTrue(first_start_entered.wait(1))
        harness.detect("RAINY")
        release_first_start.set()
        harness.wait()
        self.assertEqual(
            delivered,
            [("WINDY", "start"), ("WINDY", "end"), ("RAINY", "start")],
        )

    def test_failed_delivery_does_not_corrupt_biome_state(self):
        attempts = []

        def failing_sender(event):
            attempts.append(event)
            if event == ("WINDY", "start"):
                raise RuntimeError("webhook unavailable")

        harness = TransitionHarness(failing_sender)
        harness.detect("WINDY")
        harness.wait()
        self.assertEqual(harness.current_biome, "WINDY")
        self.assertEqual(len(harness.errors), 1)

        harness.detect("NORMAL")
        harness.wait()
        self.assertEqual(harness.current_biome, "NORMAL")
        self.assertEqual(attempts, [("WINDY", "start"), ("WINDY", "end")])


if __name__ == "__main__":
    unittest.main()
