import unittest
from unittest import mock

from requests.exceptions import ReadTimeout

from biome_tracker.mixin_detection import DetectionMixin


class BiomeDataTests(unittest.TestCase):
    def test_bundled_biome_data_loads_after_remote_timeout(self):
        detector = DetectionMixin()
        detector.config = {}
        detector.error_logging = mock.Mock()

        def get(url, timeout):
            if url.endswith("/biomes_data.json"):
                raise ReadTimeout("timed out")
            response = mock.Mock()
            response.json.return_value = {"april_fools": False}
            return response

        with mock.patch(
            "biome_tracker.mixin_detection.requests.get",
            side_effect=get,
        ) as get:
            data = detector.load_biome_data()

        self.assertIn("AURORA", data)
        self.assertEqual(data["CYBERSPACE"]["color"], "0x0A1A3D")
        get.assert_any_call(
            "https://raw.githubusercontent.com/DeeepXD/Reoteab/main/assets/biomes_data.json",
            timeout=5,
        )


if __name__ == "__main__":
    unittest.main()
