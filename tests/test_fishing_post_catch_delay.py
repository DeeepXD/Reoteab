import threading
import unittest
from unittest import mock

from biome_tracker import fishing


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += max(0.0, float(seconds))


class FishingPostCatchDelayTests(unittest.TestCase):
    def test_next_cast_follows_one_post_catch_close_settle(self):
        clock = FakeClock()
        stop_event = threading.Event()
        start = (1, 1)
        close = (2, 2)
        state = {"start_clicks": 0, "post_catch_closes": 0, "close_at": None, "next_cast_at": None}

        class FakeAutoIt:
            @staticmethod
            def mouse_click(_button, x, y, *_args, **_kwargs):
                if (x, y) == close and state["start_clicks"] >= 2:
                    state["post_catch_closes"] += 1
                    state["close_at"] = clock.now
                elif (x, y) == start:
                    state["start_clicks"] += 1
                    if state["start_clicks"] == 3:
                        state["next_cast_at"] = clock.now
                        stop_event.set()

        config = {
            "fishing_click_position": list(start),
            "fishing_close_button_pos": list(close),
            "fishing_detect_pixel": [3, 3],
            "fishing_midbar_sample_pos": [4, 4],
            "fishing_actions_delay_ms": 0,
        }
        with (
            mock.patch.object(fishing, "time", clock),
            mock.patch.object(fishing, "autoit", FakeAutoIt),
            mock.patch.object(fishing, "mss", None),
            mock.patch.object(fishing, "_get_pixel_rgb", return_value=(0, 0, 0)),
            mock.patch.object(fishing, "is_indicator_active", side_effect=lambda _pixel: state["start_clicks"] >= 1),
            mock.patch.object(fishing, "detect_colour", return_value=True),
            mock.patch.object(fishing, "_run_pre_fishing_sequence", return_value=True),
            mock.patch.object(fishing, "_run_equip_aura_before_movement", return_value=True),
            mock.patch.object(fishing, "_run_walk_to_fish_path", return_value=True),
            mock.patch.object(fishing, "_autoit_key_up", return_value=None),
        ):
            fishing.run_fishing_loop(
                stop_event=stop_event,
                config_provider=lambda: config,
                config_refresh_seconds=1000,
                print_start_stop=False,
            )

        self.assertEqual(state["post_catch_closes"], 1)
        self.assertAlmostEqual(state["next_cast_at"] - state["close_at"], 0.92, places=2)


if __name__ == "__main__":
    unittest.main()
