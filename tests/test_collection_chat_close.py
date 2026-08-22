import unittest
from unittest import mock

from biome_tracker import fishing


class CollectionChatCloseTests(unittest.TestCase):
    def test_chat_close_click_precedes_collection_click(self):
        clicks = []
        config = fishing.load_fishing_config({
            "chat_close_button": [10, 20],
            "collections_button": [30, 40],
            "exit_collections_button": [50, 60],
        })

        with (
            mock.patch.object(fishing, "_run_respawn_sequence", return_value=True),
            mock.patch.object(fishing.autoit, "mouse_click", side_effect=lambda *_args, **_kwargs: clicks.append(_args[1:3])),
        ):
            self.assertTrue(fishing._run_pre_fishing_sequence(
                cfg=config,
                sleep_interruptible=lambda *_args: True,
                should_continue=lambda: True,
                can_run=lambda: True,
            ))

        self.assertEqual(clicks, [(10, 20), (30, 40), (50, 60)])

    def test_missing_chat_close_calibration_does_not_block_collection(self):
        clicks = []
        config = fishing.load_fishing_config({
            "collections_button": [30, 40],
            "exit_collections_button": [50, 60],
        })

        with (
            mock.patch.object(fishing, "_run_respawn_sequence", return_value=True),
            mock.patch.object(fishing.autoit, "mouse_click", side_effect=lambda *_args, **_kwargs: clicks.append(_args[1:3])),
        ):
            self.assertTrue(fishing._run_pre_fishing_sequence(
                cfg=config,
                sleep_interruptible=lambda *_args: True,
                should_continue=lambda: True,
                can_run=lambda: True,
            ))

        self.assertEqual(clicks, [(30, 40), (50, 60)])


if __name__ == "__main__":
    unittest.main()
