import tempfile
import unittest
from pathlib import Path
from unittest import mock

from biome_tracker import config
from main import Api


class MacroPresetTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.patches = mock.patch.multiple(
            config,
            APPDATA_BASE=self.base,
            APPDATA_CONFIG=self.base / "config.json",
            MACRO_PRESETS_FILE=self.base / "macro_presets.json",
            MACRO_PRESET_IMAGES=self.base / "preset_images",
        )
        self.patches.start()

    def tearDown(self):
        self.patches.stop()
        self.temp_dir.cleanup()

    def test_preset_captures_all_settings_except_runtime_state_and_enforces_unique_names(self):
        source = {
            "fishing_mode": True,
            "fishing_sell_after_x_fish": "20",
            "merchant_teleporter": True,
            "Mari_Items": {"Rune": [True, 2]},
            "enable_potion_crafting": True,
            "selected_potion_file": "heavenly.json",
            "webhook_url": ["https://private.example/webhook"],
            "merchant_open_button": [600, 900],
            "biome_counts": {"NORMAL": 7},
            "session_time": "2:00:00",
        }

        result = config.create_macro_preset("Night setup", source)

        self.assertTrue(result["success"])
        duplicate = config.create_macro_preset("night SETUP", source)
        self.assertFalse(duplicate["success"])

        loaded = config.apply_macro_preset(result["preset"]["id"], {
            "webhook_url": ["keep"],
            "biome_counts": {"NORMAL": 12},
            "session_time": "3:00:00",
        })
        self.assertTrue(loaded["success"])
        self.assertEqual(loaded["config"]["fishing_sell_after_x_fish"], "20")
        self.assertTrue(loaded["config"]["merchant_teleporter"])
        self.assertTrue(loaded["config"]["enable_potion_crafting"])
        self.assertEqual(loaded["config"]["webhook_url"], ["https://private.example/webhook"])
        self.assertEqual(loaded["config"]["merchant_open_button"], [600, 900])
        self.assertEqual(loaded["config"]["biome_counts"], {"NORMAL": 12})
        self.assertEqual(loaded["config"]["session_time"], "3:00:00")

    def test_optional_image_is_copied_and_removed_with_preset(self):
        source_image = self.base / "preview.png"
        source_image.write_bytes(b"not-a-real-image")

        result = config.create_macro_preset("With image", {"fishing_mode": True}, source_image)

        self.assertTrue(result["success"])
        copied_image = Path(result["preset"]["image_path"])
        self.assertTrue(copied_image.exists())
        self.assertTrue(result["preset"]["image_data"].startswith("data:image/png;base64,"))

        deleted = config.delete_macro_preset(result["preset"]["id"])

        self.assertTrue(deleted["success"])
        self.assertFalse(copied_image.exists())
        self.assertEqual(config.list_macro_presets()["presets"], [])

    def test_loading_preset_marks_it_active(self):
        first = config.create_macro_preset("Fishing", {"fishing_mode": True})
        second = config.create_macro_preset("Merchant", {"merchant_teleporter": True})

        result = config.apply_macro_preset(first["preset"]["id"], {})

        self.assertTrue(result["success"])
        presets = config.list_macro_presets()
        self.assertEqual(presets["active_preset_id"], first["preset"]["id"])
        self.assertNotEqual(presets["active_preset_id"], second["preset"]["id"])

    def test_api_saves_the_current_ui_config_and_loads_it_into_the_tracker(self):
        tracker = mock.Mock()
        tracker.config = {"fishing_mode": False, "fishing_sell_after_x_fish": "10"}
        tracker.detection_running = False
        api = Api(tracker)
        ui_config = {"fishing_mode": True, "fishing_sell_after_x_fish": "25"}

        saved = api.save_macro_preset("Current UI", ui_config)
        self.assertTrue(saved["success"])

        tracker.config = {"fishing_mode": False, "fishing_sell_after_x_fish": "5"}
        loaded = api.load_macro_preset(saved["preset"]["id"])

        self.assertTrue(loaded["success"])
        self.assertTrue(tracker.config["fishing_mode"])
        self.assertEqual(tracker.config["fishing_sell_after_x_fish"], "25")


if __name__ == "__main__":
    unittest.main()
