import importlib.util
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

    def test_existing_coteab_data_is_used_as_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            legacy = Path(directory) / "CoteabMacro"
            legacy.mkdir()
            module = load_config(Path(directory))
            self.assertEqual(module.APPDATA_BASE, legacy)

    def test_reoteab_path_is_preferred_when_both_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            reoteab = Path(directory) / "Reoteab"
            reoteab.mkdir()
            (Path(directory) / "CoteabMacro").mkdir()
            module = load_config(Path(directory))
            self.assertEqual(module.APPDATA_BASE, reoteab)


if __name__ == "__main__":
    unittest.main()
