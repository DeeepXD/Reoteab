import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from main import Api


class _Window:
    def __init__(self, path):
        self.path = str(path)

    def create_file_dialog(self, *_args, **_kwargs):
        return [self.path]


class _Tracker:
    def __init__(self, config):
        self.config = config
        self.detection_running = False


class CalibrationImportTests(unittest.TestCase):
    def _import_file(self, contents, tracker=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calibrations.json"
            path.write_text(contents, encoding="utf-8")
            api = Api(tracker)
            api._window = _Window(path)
            return api.import_calibration_data_from_file()

    def test_imports_current_export_preset_format(self):
        result = self._import_file(json.dumps({
            "presets": [{
                "resolution": "",
                "scale": "",
                "mode": "",
                "calibrations": {"merchant_open_button": [651, 943]},
            }],
        }))

        self.assertTrue(result["success"])
        self.assertEqual(result["data"], {"merchant_open_button": [651, 943]})

    def test_imports_legacy_flat_calibration_format(self):
        calibrations = {
            "merchant_open_button": [404, 662],
            "merchant_dialogue_box": [872, 555],
        }
        result = self._import_file(json.dumps(calibrations))

        self.assertTrue(result["success"])
        self.assertEqual(result["data"], calibrations)

    def test_malformed_json_returns_error_without_changing_existing_values(self):
        tracker = _Tracker({"merchant_open_button": [651, 943]})
        result = self._import_file("{not valid json", tracker)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid JSON file")
        self.assertEqual(tracker.config, {"merchant_open_button": [651, 943]})

    def test_missing_calibrations_returns_error(self):
        result = self._import_file(json.dumps({"presets": [{"resolution": "1920x1080"}]}))

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid calibration file: missing calibrations")

    def test_imported_calibrations_are_saved_to_the_active_config(self):
        tracker = _Tracker({"merchant_open_button": [100, 100], "unchanged": True})
        result = self._import_file(json.dumps({"merchant_open_button": [651, 943]}), tracker)
        merged = {**tracker.config, **result["data"]}

        with mock.patch("main.save_config"):
            Api(tracker).save_config(merged)

        self.assertEqual(tracker.config["merchant_open_button"], [651, 943])
        self.assertTrue(tracker.config["unchanged"])


if __name__ == "__main__":
    unittest.main()
