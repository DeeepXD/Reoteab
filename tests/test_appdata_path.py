import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


CONFIG_PATH = Path(__file__).resolve().parents[1] / "biome_tracker" / "config.py"


def load_config(local_appdata: Path):
    spec = importlib.util.spec_from_file_location("reoteab_appdata_config", CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, {"LOCALAPPDATA": str(local_appdata)}):
        spec.loader.exec_module(module)
    return module


class AppDataPathTests(unittest.TestCase):
    def test_new_install_uses_reoteab_path(self):
        with tempfile.TemporaryDirectory() as directory:
            module = load_config(Path(directory))
            self.assertEqual(module.APPDATA_BASE, Path(directory) / "Reoteab")

    def test_existing_coteab_data_is_imported_into_reoteab(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "CoteabMacro"
            legacy.mkdir()
            legacy_config = legacy / "config.json"
            legacy_config.write_text(json.dumps({"merchant_open_button": [1, 2]}), encoding="utf-8")
            module = load_config(Path(directory))
            module.ensure_workspace_files()
            self.assertEqual(module.APPDATA_BASE, Path(directory) / "Reoteab")
            self.assertEqual(module.load_config()["merchant_open_button"], [1, 2])
            self.assertEqual(
                legacy_config.read_text(encoding="utf-8"),
                json.dumps({"merchant_open_button": [1, 2]}),
            )

    def test_reoteab_path_is_preferred_when_both_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            reoteab = Path(directory) / "Reoteab"
            reoteab.mkdir()
            (Path(directory) / "CoteabMacro").mkdir()
            module = load_config(Path(directory))
            self.assertEqual(module.APPDATA_BASE, reoteab)

    def test_existing_reoteab_config_wins_over_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reoteab = root / "Reoteab"
            reoteab.mkdir()
            (reoteab / "config.json").write_text(json.dumps({"source": "reoteab"}), encoding="utf-8")
            legacy = root / "CoteabMacro"
            legacy.mkdir()
            (legacy / "config.json").write_text(json.dumps({"source": "legacy"}), encoding="utf-8")

            module = load_config(root)
            module.ensure_workspace_files()

            self.assertEqual(module.load_config()["source"], "reoteab")

    def test_portable_config_still_wins_over_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "CoteabMacro"
            legacy.mkdir()
            (legacy / "config.json").write_text(json.dumps({"source": "legacy"}), encoding="utf-8")
            portable_config = root / "portable-config.json"
            portable_config.write_text(json.dumps({"source": "portable"}), encoding="utf-8")

            module = load_config(root)
            module.EXE_CONFIG = portable_config
            module.ensure_workspace_files()

            self.assertEqual(module.load_config()["source"], "portable")

    def test_malformed_legacy_config_is_not_imported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "CoteabMacro"
            legacy.mkdir()
            legacy_config = legacy / "config.json"
            legacy_config.write_text("{not valid json", encoding="utf-8")

            module = load_config(root)
            module.ensure_workspace_files()

            self.assertEqual(
                json.loads((root / "Reoteab" / "config.json").read_text(encoding="utf-8")),
                {},
            )
            self.assertEqual(legacy_config.read_text(encoding="utf-8"), "{not valid json")

    def test_config_save_and_workspace_files_use_reoteab(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "CoteabMacro"
            legacy.mkdir()
            module = load_config(root)

            module.ensure_workspace_files()
            module.save_config({"example": True})

            reoteab = root / "Reoteab"
            self.assertTrue((reoteab / "config.json").exists())
            self.assertTrue((reoteab / "logs").is_dir())
            self.assertTrue((reoteab / "images").is_dir())
            self.assertTrue((reoteab / "paths").is_dir())
            self.assertFalse((legacy / "config.json").exists())

    def test_legacy_config_without_reconnect_setting_uses_current_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "CoteabMacro"
            legacy.mkdir()
            (legacy / "config.json").write_text(json.dumps({"chat_close_button": [1, 2]}), encoding="utf-8")

            module = load_config(root)
            module.ensure_workspace_files()

            self.assertEqual(module.load_config()["chat_close_button"], [1, 2])
            self.assertNotIn("close_chat_after_reconnect", module.load_config())


if __name__ == "__main__":
    unittest.main()
