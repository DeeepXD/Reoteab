import tempfile
import unittest
from pathlib import Path
from unittest import mock

from biome_tracker import config


class MacroPresetTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.patches = mock.patch.multiple(
            config,
            APPDATA_BASE=self.base,
            MACRO_PRESETS_FILE=self.base / "macro_presets.json",
            MACRO_PRESET_IMAGES=self.base / "preset_images",
        )
        self.patches.start()

    def tearDown(self):
        self.patches.stop()
        self.temp_dir.cleanup()

    def test_preset_captures_only_macro_settings_and_enforces_unique_names(self):
        source = {
            "fishing_mode": True,
            "fishing_sell_after_x_fish": "20",
            "merchant_teleporter": True,
            "Mari_Items": {"Rune": [True, 2]},
            "enable_potion_crafting": True,
            "selected_potion_file": "heavenly.json",
            "webhook_url": ["https://private.example/webhook"],
            "merchant_open_button": [600, 900],
        }

        result = config.create_macro_preset("Night setup", source)

        self.assertTrue(result["success"])
        duplicate = config.create_macro_preset("night SETUP", source)
        self.assertFalse(duplicate["success"])

        loaded = config.apply_macro_preset(result["preset"]["id"], {"webhook_url": ["keep"]})
        self.assertTrue(loaded["success"])
        self.assertEqual(loaded["config"]["fishing_sell_after_x_fish"], "20")
        self.assertTrue(loaded["config"]["merchant_teleporter"])
        self.assertTrue(loaded["config"]["enable_potion_crafting"])
        self.assertEqual(loaded["config"]["webhook_url"], ["keep"])
        self.assertNotIn("merchant_open_button", loaded["config"])

    def test_optional_image_is_copied_and_removed_with_preset(self):
        source_image = self.base / "preview.png"
        source_image.write_bytes(b"not-a-real-image")

        result = config.create_macro_preset("With image", {"fishing_mode": True}, source_image)

        self.assertTrue(result["success"])
        copied_image = Path(result["preset"]["image_path"])
        self.assertTrue(copied_image.exists())

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


if __name__ == "__main__":
    unittest.main()
