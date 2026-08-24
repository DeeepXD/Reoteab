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


class FishingPreFishCloseTests(unittest.TestCase):
    def _run_initial_fish_click(self, config):
        clock = FakeClock()
        stop_event = threading.Event()
        clicks = []
        fish_button = tuple(config["fishing_click_position"])

        class FakeAutoIt:
            @staticmethod
            def mouse_click(_button, x, y, *_args, **_kwargs):
                clicks.append((x, y))
                if (x, y) == fish_button:
                    stop_event.set()

        with (
            mock.patch.object(fishing, "time", clock),
            mock.patch.object(fishing, "autoit", FakeAutoIt),
            mock.patch.object(fishing, "mss", None),
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

        return clicks

    def test_pre_fish_close_clicks_before_fishing_button(self):
        config = {
            "fishing_click_position": [10, 20],
            "fishing_pre_fish_close_button": [30, 40],
        }

        clicks = self._run_initial_fish_click(config)

        self.assertEqual(clicks[-2:], [(30, 40), (10, 20)])

    def test_missing_pre_fish_close_calibration_keeps_fishing_button_click(self):
        config = {
            "fishing_click_position": [10, 20],
        }

        clicks = self._run_initial_fish_click(config)

        self.assertEqual(clicks[-1], (10, 20))
        self.assertNotIn((0, 0), clicks)

    def test_missing_pre_fish_close_calibration_normalizes_to_disabled(self):
        config = fishing.load_fishing_config({"fishing_click_position": [10, 20]})

        self.assertEqual(config["fishing_pre_fish_close_button"], (0, 0))


if __name__ == "__main__":
    unittest.main()
