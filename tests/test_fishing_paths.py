import threading
import unittest
from unittest import mock

from biome_tracker import fishing


def _event_signature(events):
    return [
        (event["type"], event.get("key"), event.get("delta"), event["t"])
        for event in events
    ]


def _play_path(events, speed_multiplier=1.0):
    clock = [0.0]
    actions = []

    def sleep_interruptible(seconds, _poll):
        clock[0] += seconds
        return True

    def key_down(key):
        actions.append(("down", key, clock[0]))

    def key_up(key):
        actions.append(("up", key, clock[0]))

    with (
        mock.patch.object(fishing, "_autoit_key_down", side_effect=key_down),
        mock.patch.object(fishing, "_autoit_key_up", side_effect=key_up),
        mock.patch.object(fishing.autoit, "mouse_wheel", create=True),
        mock.patch.object(fishing.time, "sleep"),
    ):
        assert fishing._run_recorded_events(
            events=events,
            sleep_interruptible=sleep_interruptible,
            should_continue=lambda: True,
            can_run=lambda: True,
            speed_multiplier=speed_multiplier,
        )

    return actions


def _next_action(actions, start, kind, key):
    for index in range(start + 1, len(actions)):
        if actions[index][:2] == (kind, key):
            return index, actions[index][2]
    raise AssertionError(f"Missing {kind} {key} after index {start}")


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

    def test_non_vip_routes_include_climb_settle(self):
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
                ("key_down", "e", None, 16.635),
                ("key_up", "e", None, 16.675),
                ("key_up", "e", None, 17.055),
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

    def test_vip_climb_keeps_its_existing_landing_buffer(self):
        actions = _play_path(fishing.WALK_TO_FISH_EVENTS)
        space_down, _ = _next_action(actions, -1, "down", "space")
        space_up, _ = _next_action(actions, space_down, "up", "space")
        w_up, _ = _next_action(actions, space_up, "up", "w")
        _, a_down_at = _next_action(actions, w_up, "down", "a")

        self.assertAlmostEqual(actions[space_up][2] - actions[space_down][2], 0.985)
        self.assertAlmostEqual(actions[w_up][2] - actions[space_up][2], 0.5)
        self.assertAlmostEqual(a_down_at - actions[w_up][2], 0.3)

    def test_non_vip_turns_immediately_after_landing(self):
        actions = _play_path(fishing.NON_VIP_WALK_TO_FISH_EVENTS)
        space_down, _ = _next_action(actions, -1, "down", "space")
        space_up, _ = _next_action(actions, space_down, "up", "space")
        w_up, _ = _next_action(actions, space_up, "up", "w")
        _, a_down_at = _next_action(actions, w_up, "down", "a")

        self.assertAlmostEqual(actions[space_up][2] - actions[space_down][2], 1.236)
        self.assertAlmostEqual(actions[w_up][2] - actions[space_up][2], 0.472)
        self.assertAlmostEqual(a_down_at - actions[w_up][2], 0.0)

    def test_non_vip_post_climb_tail_keeps_the_recorded_turn_timing(self):
        actions = _play_path(fishing.NON_VIP_WALK_TO_FISH_EVENTS)
        space_down, _ = _next_action(actions, -1, "down", "space")
        space_up, _ = _next_action(actions, space_down, "up", "space")
        w_up, _ = _next_action(actions, space_up, "up", "w")
        a_down, a_down_at = _next_action(actions, w_up, "down", "a")
        a_up, a_up_at = _next_action(actions, a_down, "up", "a")
        w_down, w_down_at = _next_action(actions, a_up, "down", "w")
        _, w_up_at = _next_action(actions, w_down, "up", "w")

        self.assertAlmostEqual(a_up_at - a_down_at, 1.372)
        self.assertAlmostEqual(w_down_at - a_up_at, 0.839)
        self.assertAlmostEqual(w_up_at - w_down_at, 3.137)

    def test_playback_multiplier_scales_climb_space_and_settle_timing(self):
        multiplier = 1.25
        vip_actions = _play_path(fishing.WALK_TO_FISH_EVENTS, multiplier)
        vip_space_down, _ = _next_action(vip_actions, -1, "down", "space")
        vip_space_up, _ = _next_action(vip_actions, vip_space_down, "up", "space")
        vip_w_up, _ = _next_action(vip_actions, vip_space_up, "up", "w")
        _, vip_a_down_at = _next_action(vip_actions, vip_w_up, "down", "a")

        self.assertAlmostEqual(vip_actions[vip_space_up][2] - vip_actions[vip_space_down][2], 0.985 * multiplier)
        self.assertAlmostEqual(vip_actions[vip_w_up][2] - vip_actions[vip_space_up][2], 0.5 * multiplier)
        self.assertAlmostEqual(vip_a_down_at - vip_actions[vip_w_up][2], 0.3 * multiplier)

        non_vip_actions = _play_path(fishing.NON_VIP_WALK_TO_FISH_EVENTS, multiplier)
        non_vip_space_down, _ = _next_action(non_vip_actions, -1, "down", "space")
        non_vip_space_up, _ = _next_action(non_vip_actions, non_vip_space_down, "up", "space")
        non_vip_w_up, _ = _next_action(non_vip_actions, non_vip_space_up, "up", "w")
        _, non_vip_a_down_at = _next_action(non_vip_actions, non_vip_w_up, "down", "a")

        self.assertAlmostEqual(non_vip_actions[non_vip_space_up][2] - non_vip_actions[non_vip_space_down][2], 1.236 * multiplier)
        self.assertAlmostEqual(non_vip_actions[non_vip_w_up][2] - non_vip_actions[non_vip_space_up][2], 0.472 * multiplier)
        self.assertAlmostEqual(non_vip_a_down_at - non_vip_actions[non_vip_w_up][2], 0.0)

    def test_cancellation_during_climb_releases_held_keys(self):
        released = []

        def sleep_interruptible(seconds, _poll):
            return seconds < 0.96

        with (
            mock.patch.object(fishing, "_autoit_key_down"),
            mock.patch.object(fishing, "_autoit_key_up", side_effect=released.append),
            mock.patch.object(fishing.autoit, "mouse_wheel", create=True),
            mock.patch.object(fishing.time, "sleep"),
        ):
            self.assertFalse(
                fishing._run_recorded_events(
                    events=fishing.WALK_TO_FISH_EVENTS,
                    sleep_interruptible=sleep_interruptible,
                    should_continue=lambda: True,
                    can_run=lambda: True,
                )
            )

        self.assertIn("space", released)
        self.assertIn("w", released)
        self.assertTrue({"w", "a", "s", "d", "space"}.issubset(released))

    def test_cancellation_after_space_down_releases_keys(self):
        released = []
        space_down = [False]

        def key_down(key):
            if key == "space":
                space_down[0] = True

        with (
            mock.patch.object(fishing, "_autoit_key_down", side_effect=key_down),
            mock.patch.object(fishing, "_autoit_key_up", side_effect=released.append),
            mock.patch.object(fishing.autoit, "mouse_wheel", create=True),
            mock.patch.object(fishing.time, "sleep"),
        ):
            self.assertFalse(
                fishing._run_recorded_events(
                    events=fishing.WALK_TO_FISH_EVENTS,
                    sleep_interruptible=lambda *_args: True,
                    should_continue=lambda: not space_down[0],
                    can_run=lambda: True,
                )
            )

        self.assertTrue(space_down[0])
        self.assertIn("space", released)
        self.assertIn("w", released)

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
