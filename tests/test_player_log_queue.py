import queue
import unittest

from biome_tracker.mixin_actions import ActionsMixin
from biome_tracker.mixin_detection import DetectionMixin


class _PlayerLogQueueHarness:
    def __init__(self):
        self.player_log_queue = queue.Queue(maxsize=2)
        self._player_log_queue_overflow_reported = False
        self.logs = []

    def append_log(self, message):
        self.logs.append(message)


class PlayerLogQueueTests(unittest.TestCase):
    def test_player_log_delivery_queue_is_bounded(self):
        harness = _PlayerLogQueueHarness()

        for index in range(10):
            ActionsMixin._enqueue_player_embed(harness, {"index": index})

        self.assertEqual(harness.player_log_queue.qsize(), 2)
        self.assertEqual(len(harness.logs), 1)
        self.assertIn("queue is full", harness.logs[0])

    def test_stopping_with_a_full_queue_does_not_block(self):
        harness = _PlayerLogQueueHarness()
        harness.player_log_sender_running = True
        harness.player_log_queue.put_nowait({"first": True})
        harness.player_log_queue.put_nowait({"second": True})

        DetectionMixin._stop_player_log_sender_thread(harness)

        self.assertFalse(harness.player_log_sender_running)
        self.assertEqual(harness.player_log_queue.qsize(), 2)


if __name__ == "__main__":
    unittest.main()
