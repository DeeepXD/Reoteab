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
    def __init__(self):
        self.current_biome = "NORMAL"
        self.events = []
        self.errors = []
        self.generation = 0
        self.active = False
        self.dispatcher = None

    def start(self):
        self.generation += 1
        self.active = True
        self.dispatcher = BiomeTransitionDispatcher(
            self.generation,
            self.is_active,
            self.errors.append,
        )

    def stop(self):
        self.active = False
        self.dispatcher.stop()
        self.dispatcher._worker.join(1)

    def is_active(self, generation):
        return self.active and generation == self.generation

    def detect(self, biome):
        if biome == self.current_biome:
            return
        previous_biome = self.current_biome
        self.current_biome = biome
        generation = self.generation
        self.dispatcher.submit(self._deliver, previous_biome, biome, generation)

    def _deliver(self, previous_biome, biome, generation):
        if not self.is_active(generation):
            return
        self.events.extend(biome_webhook_events(previous_biome, biome))

    def wait(self):
        self.dispatcher.wait_for_idle()


class BiomeTransitionTests(unittest.TestCase):
    def test_start_event_emitted_once(self):
        harness = TransitionHarness()
        harness.start()
        harness.detect("WINDY")
        harness.detect("WINDY")
        harness.wait()
        self.assertEqual(harness.events, [("WINDY", "start")])
        harness.stop()

    def test_a_to_b_emits_end_then_start_in_order(self):
        harness = TransitionHarness()
        harness.start()
        harness.detect("WINDY")
        harness.detect("RAINY")
        harness.wait()
        self.assertEqual(
            harness.events,
            [("WINDY", "start"), ("WINDY", "end"), ("RAINY", "start")],
        )
        harness.stop()

    def test_stopped_session_drops_queued_transitions(self):
        active = {"value": True}
        entered = threading.Event()
        release = threading.Event()
        delivered = []

        def is_active(_generation):
            return active["value"]

        def block():
            entered.set()
            release.wait(1)

        dispatcher = BiomeTransitionDispatcher(1, is_active)
        dispatcher.submit(block)
        self.assertTrue(entered.wait(1))
        dispatcher.submit(delivered.append, ("WINDY", "start"))
        active["value"] = False
        dispatcher.stop()
        release.set()
        dispatcher._worker.join(1)

        self.assertEqual(delivered, [])

    def test_repeated_sessions_do_not_keep_dispatcher_workers(self):
        harness = TransitionHarness()
        for _ in range(3):
            harness.start()
            dispatcher = harness.dispatcher
            harness.detect("WINDY")
            harness.wait()
            harness.stop()
            self.assertFalse(dispatcher._worker.is_alive())


if __name__ == "__main__":
    unittest.main()
