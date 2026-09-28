import threading
import time
import unittest

from biome_tracker.base_support import ActionScheduler


class _Owner:
    def error_logging(self, *_args, **_kwargs):
        pass


class ActionSchedulerTests(unittest.TestCase):
    def test_unique_periodic_action_does_not_grow_queue(self):
        scheduler = ActionScheduler(_Owner())
        entered = threading.Event()
        release = threading.Event()

        def block():
            entered.set()
            release.wait(1)

        scheduler.enqueue_action(block, name="block", priority=0)
        self.assertTrue(entered.wait(1))
        self.assertTrue(scheduler.enqueue_action(lambda: None, name="periodical:aura", unique=True))
        for _ in range(1000):
            self.assertFalse(scheduler.enqueue_action(lambda: None, name="periodical:aura", unique=True))
        self.assertEqual(scheduler._pq.qsize(), 1)

        release.set()
        for _ in range(100):
            if "periodical:aura" not in scheduler._pending_names:
                break
            time.sleep(0.01)
        self.assertNotIn("periodical:aura", scheduler._pending_names)
        scheduler.stop()


if __name__ == "__main__":
    unittest.main()
