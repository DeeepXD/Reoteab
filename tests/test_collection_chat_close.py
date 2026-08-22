import threading
import unittest
from unittest import mock

from biome_tracker import fishing


class CollectionChatCloseTests(unittest.TestCase):
    def test_initial_collection_does_not_click_chat_close_calibration(self):
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

        self.assertEqual(clicks, [(30, 40), (50, 60)])

    def test_post_reconnect_collection_clicks_chat_close_first(self):
        clicks = []
        config = fishing.load_fishing_config({
            "chat_close_button": [10, 20],
            "collections_button": [30, 40],
            "exit_collections_button": [50, 60],
        })

        with (
            mock.patch.object(fishing, "_run_respawn_sequence", return_value=True),
            mock.patch.object(fishing, "_run_equip_aura_before_movement", return_value=True),
            mock.patch.object(fishing, "_run_walk_to_sell_fish_path", return_value=True),
            mock.patch.object(fishing.autoit, "mouse_click", side_effect=lambda *_args, **_kwargs: clicks.append(_args[1:3])),
        ):
            self.assertTrue(fishing._run_sell_fish_sequence(
                cfg=config,
                fish_sell_count=1,
                sleep_interruptible=lambda *_args: True,
                should_continue=lambda: True,
                can_run=lambda: True,
                post_reconnect_cleanup=True,
            ))

        self.assertEqual(clicks[:3], [(10, 20), (30, 40), (50, 60)])

    def test_ordinary_sell_does_not_repeat_post_reconnect_chat_close(self):
        clicks = []
        config = fishing.load_fishing_config({
            "chat_close_button": [10, 20],
            "collections_button": [30, 40],
            "exit_collections_button": [50, 60],
        })

        with (
            mock.patch.object(fishing, "_run_respawn_sequence", return_value=True),
            mock.patch.object(fishing, "_run_equip_aura_before_movement", return_value=True),
            mock.patch.object(fishing, "_run_walk_to_sell_fish_path", return_value=True),
            mock.patch.object(fishing.autoit, "mouse_click", side_effect=lambda *_args, **_kwargs: clicks.append(_args[1:3])),
        ):
            self.assertTrue(fishing._run_sell_fish_sequence(
                cfg=config,
                fish_sell_count=1,
                sleep_interruptible=lambda *_args: True,
                should_continue=lambda: True,
                can_run=lambda: True,
            ))

        self.assertEqual(clicks[:2], [(30, 40), (50, 60)])

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
            self.assertTrue(fishing._run_sell_fish_sequence(
                cfg=config,
                fish_sell_count=1,
                sleep_interruptible=lambda *_args: True,
                should_continue=lambda: True,
                can_run=lambda: True,
                post_reconnect_cleanup=True,
            ))

        self.assertEqual(clicks[:2], [(30, 40), (50, 60)])

    def test_reconnect_forced_sell_consumes_cleanup_once(self):
        stop_event = threading.Event()
        calls = []
        runtime_state = {"force_sell_on_next_cycle": True}

        def run_sell(**kwargs):
            calls.append(kwargs["post_reconnect_cleanup"])
            stop_event.set()
            return True

        with mock.patch.object(fishing, "_run_sell_fish_sequence", side_effect=run_sell):
            fishing.run_fishing_loop(
                stop_event=stop_event,
                config_provider=lambda: {"fishing_sell_how_many_fish": 1},
                print_start_stop=False,
                runtime_state=runtime_state,
            )

        self.assertEqual(calls, [True])
        self.assertFalse(runtime_state["force_sell_on_next_cycle"])


if __name__ == "__main__":
    unittest.main()
