import importlib.util
import sys
import types
import unittest
from pathlib import Path


PACKAGE_NAME = "runtime_log_test_package"
PACKAGE = types.ModuleType(PACKAGE_NAME)
PACKAGE.__path__ = []
sys.modules[PACKAGE_NAME] = PACKAGE
sys.modules[f"{PACKAGE_NAME}.base_support"] = types.ModuleType(f"{PACKAGE_NAME}.base_support")

TRANSITIONS_PATH = Path(__file__).parents[1] / "biome_tracker" / "biome_transitions.py"
TRANSITIONS_SPEC = importlib.util.spec_from_file_location(f"{PACKAGE_NAME}.biome_transitions", TRANSITIONS_PATH)
TRANSITIONS_MODULE = importlib.util.module_from_spec(TRANSITIONS_SPEC)
assert TRANSITIONS_SPEC.loader is not None
sys.modules[TRANSITIONS_SPEC.name] = TRANSITIONS_MODULE
TRANSITIONS_SPEC.loader.exec_module(TRANSITIONS_MODULE)

DETECTION_PATH = Path(__file__).parents[1] / "biome_tracker" / "mixin_detection.py"
DETECTION_SPEC = importlib.util.spec_from_file_location(f"{PACKAGE_NAME}.mixin_detection", DETECTION_PATH)
DETECTION_MODULE = importlib.util.module_from_spec(DETECTION_SPEC)
assert DETECTION_SPEC.loader is not None
sys.modules[DETECTION_SPEC.name] = DETECTION_MODULE
DETECTION_SPEC.loader.exec_module(DETECTION_MODULE)
DetectionMixin = DETECTION_MODULE.DetectionMixin


class RuntimeLogHarness(DetectionMixin):
    def __init__(self):
        self.logs = []


class RuntimeLogTests(unittest.TestCase):
    def test_runtime_log_history_is_bounded(self):
        harness = RuntimeLogHarness()
        for index in range(harness.MAX_RUNTIME_LOGS + 10):
            harness._append_runtime_log(str(index))

        self.assertEqual(len(harness.logs), harness.MAX_RUNTIME_LOGS)
        self.assertEqual(harness.logs[0], "10")
        self.assertEqual(harness.logs[-1], str(harness.MAX_RUNTIME_LOGS + 9))


if __name__ == "__main__":
    unittest.main()
