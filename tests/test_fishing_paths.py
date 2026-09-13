import threading
import unittest
from unittest import mock

from biome_tracker import fishing


def _event_signature(events):
    return [
        (event["type"], event.get("key"), event.get("delta"), event["t"])
        for event in events
    ]


class FishingPathTests(unittest.TestCase):
    def test_vip_routes_match_solrich(self):
        flarg_path = [
            ("mouse_wheel", None, 80, 0.0),
            ("mouse_wheel", None, -15, 0.25),
            ("key_down", "w", None, 0.5),
            ("key_up", "w", None, 3.5),
            ("key_down", "a", None, 4.0),
            ("key_down", "w", None, 6.5),
            ("key_up", "w", None, 10.5),
            ("key_up", "a", None, 10.5),
            ("key_down", "s", None, 12.5),
            ("key_up", "s", None, 12.8),
            ("key_down", "space", None, 13.1),
            ("key_down", "w", None, 13.125),
            ("key_up", "space", None, 14.085),
            ("key_up", "w", None, 14.585),
        ]

        self.assertEqual(_event_signature(fishing._VIP_WALK_TO_FLARG_EVENTS), flarg_path)
        self.assertEqual(
            _event_signature(fishing.WALK_TO_SELL_FISH_EVENTS),
            flarg_path + [
                ("key_down", "e", None, 14.885),
                ("key_up", "e", None, 14.925),
                ("key_up", "e", None, 15.305),
            ],
        )
        self.assertEqual(
            _event_signature(fishing.WALK_TO_FISH_EVENTS),
            flarg_path + [
                ("key_down", "a", None, 14.885),
                ("key_up", "a", None, 16.005),
                ("key_down", "w", None, 16.08),
                ("key_up", "w", None, 18.43),
            ],
        )

    def test_non_vip_routes_match_solrich(self):
        flarg_path = [
            ("mouse_wheel", None, 80, 0.0),
            ("mouse_wheel", None, -15, 0.25),
            ("key_down", "w", None, 0.5),
            ("key_up", "w", None, 4.128),
            ("key_down", "a", None, 4.943),
            ("key_down", "w", None, 6.978),
            ("key_up", "a", None, 11.409),
            ("key_down", "a", None, 11.665),
            ("key_up", "a", None, 11.841),
            ("key_down", "a", None, 11.941),
            ("key_up", "a", None, 12.094),
            ("key_down", "a", None, 12.158),
            ("key_up", "a", None, 12.28),
            ("key_down", "a", None, 12.343),
            ("key_up", "a", None, 12.588),
            ("key_up", "w", None, 12.646),
            ("key_down", "s", None, 13.528),
            ("key_up", "s", None, 13.708),
            ("key_down", "w", None, 14.677),
            ("key_down", "space", None, 14.677),
            ("key_up", "space", None, 15.913),
            ("key_up", "w", None, 16.385),
        ]

        self.assertEqual(_event_signature(fishing._NON_VIP_WALK_TO_FLARG_EVENTS), flarg_path)
        self.assertEqual(
            _event_signature(fishing.NON_VIP_WALK_TO_SELL_FISH_EVENTS),
            flarg_path + [
                ("key_down", "e", None, 16.385),
                ("key_up", "e", None, 16.425),
                ("key_up", "e", None, 16.805),
            ],
        )
        self.assertEqual(
            _event_signature(fishing.NON_VIP_WALK_TO_FISH_EVENTS),
            flarg_path + [
                ("key_down", "a", None, 16.385),
                ("key_up", "a", None, 17.757),
                ("key_down", "w", None, 18.596),
                ("key_up", "w", None, 21.733),
            ],
        )

    def test_path_helpers_select_vip_and_non_vip_routes(self):
        callbacks = {
            "sleep_interruptible": mock.Mock(return_value=True),
            "should_continue": mock.Mock(return_value=True),
            "can_run": mock.Mock(return_value=True),
        }
        cases = [
            (fishing._run_walk_to_fish_path, False, fishing.WALK_TO_FISH_EVENTS),
            (fishing._run_walk_to_fish_path, True, fishing.NON_VIP_WALK_TO_FISH_EVENTS),
            (fishing._run_walk_to_sell_fish_path, False, fishing.WALK_TO_SELL_FISH_EVENTS),
            (fishing._run_walk_to_sell_fish_path, True, fishing.NON_VIP_WALK_TO_SELL_FISH_EVENTS),
        ]

        for path_function, non_vip, expected_events in cases:
            with self.subTest(path=path_function.__name__, non_vip=non_vip):
                with mock.patch.object(fishing, "_run_recorded_events", return_value=True) as run_events:
                    self.assertTrue(
                        path_function(
                            **callbacks,
                            non_vip=non_vip,
                            speed_multiplier=1.15,
                        )
                    )
                self.assertIs(run_events.call_args.kwargs["events"], expected_events)
                self.assertEqual(run_events.call_args.kwargs["speed_multiplier"], 1.15)

    def test_non_vip_setting_uses_current_config_normalization(self):
        config = fishing.load_fishing_config({"non_vip_movement_path": True})

        self.assertTrue(config["non_vip_movement_path"])

    def test_initial_fishing_uses_normalized_non_vip_route(self):
        stop_event = threading.Event()

        def run_path(**kwargs):
            stop_event.set()
            return True

        with (
            mock.patch.object(fishing, "_run_pre_fishing_sequence", return_value=True),
            mock.patch.object(fishing, "_run_equip_aura_before_movement", return_value=True),
            mock.patch.object(fishing, "_run_walk_to_fish_path", side_effect=run_path) as walk_path,
            mock.patch.object(fishing, "_autoit_key_up", return_value=None),
        ):
            fishing.run_fishing_loop(
                stop_event=stop_event,
                config_provider=lambda: {
                    "non_vip_movement_path": True,
                    "fishing_playback_multiplier": 1.15,
                },
                print_start_stop=False,
            )

        self.assertTrue(walk_path.call_args.kwargs["non_vip"])
        self.assertEqual(walk_path.call_args.kwargs["speed_multiplier"], 1.15)

    def test_sell_sequence_uses_normalized_non_vip_route(self):
        config = fishing.load_fishing_config({
            "non_vip_movement_path": True,
            "fishing_playback_multiplier": 1.15,
        })

        with (
            mock.patch.object(fishing, "_run_respawn_sequence", return_value=True),
            mock.patch.object(fishing, "_run_equip_aura_before_movement", return_value=True),
            mock.patch.object(fishing, "_run_walk_to_sell_fish_path", return_value=True) as walk_path,
            mock.patch.object(fishing.autoit, "mouse_click", create=True),
        ):
            self.assertTrue(
                fishing._run_sell_fish_sequence(
                    cfg=config,
                    fish_sell_count=1,
                    sleep_interruptible=lambda *_args: True,
                    should_continue=lambda: True,
                    can_run=lambda: True,
                )
            )

        self.assertTrue(walk_path.call_args.kwargs["non_vip"])
        self.assertEqual(walk_path.call_args.kwargs["speed_multiplier"], 1.15)


if __name__ == "__main__":
    unittest.main()
