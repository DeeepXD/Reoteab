import importlib.util
import unittest
from pathlib import Path


CONFIG_PATH = Path(__file__).parents[1] / "biome_tracker" / "config.py"
SPEC = importlib.util.spec_from_file_location("reoteab_config", CONFIG_PATH)
CONFIG_MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CONFIG_MODULE)
validate_merchant_settings = CONFIG_MODULE.validate_merchant_settings


class MerchantNumericSettingsTests(unittest.TestCase):
    def validate(self, **overrides):
        config = {
            "merchant_extra_slot": "0",
            "inventory_click_delay": "650",
            "jester_exchange_count": 0,
            "jester_exchange_threshold": "3",
            "Mari_Items": {},
            "Jester_Items": {},
            "Jester_Exchange_Items": {},
            "Rin_Items": {},
        }
        config.update(overrides)
        return validate_merchant_settings(config)

    def test_merchant_extra_slot_blank_malformed_zero_and_valid(self):
        self.assertEqual(self.validate(merchant_extra_slot="")[0]["merchant_extra_slot"], 0)
        self.assertEqual(self.validate(merchant_extra_slot="nope")[0]["merchant_extra_slot"], 0)
        self.assertEqual(self.validate(merchant_extra_slot="0")[0]["merchant_extra_slot"], 0)
        self.assertEqual(self.validate(merchant_extra_slot="2")[0]["merchant_extra_slot"], 2)

    def test_merchant_extra_slot_missing_uses_zero(self):
        config = self.validate()[0]
        config.pop("merchant_extra_slot")
        validated, warnings = validate_merchant_settings(config)
        self.assertEqual(validated["merchant_extra_slot"], 0)
        self.assertTrue(any("merchant_extra_slot" in warning for warning in warnings))

    def test_inventory_delay_blank_malformed_missing_zero_and_valid(self):
        self.assertEqual(self.validate(inventory_click_delay="")[0]["inventory_click_delay"], 0)
        self.assertEqual(self.validate(inventory_click_delay="slow")[0]["inventory_click_delay"], 0)
        self.assertEqual(self.validate(inventory_click_delay="0")[0]["inventory_click_delay"], 0)
        self.assertEqual(self.validate(inventory_click_delay="650")[0]["inventory_click_delay"], 650)
        config = self.validate()[0]
        config.pop("inventory_click_delay")
        self.assertEqual(validate_merchant_settings(config)[0]["inventory_click_delay"], 0)

    def test_jester_exchange_values_blank_malformed_missing_zero_and_valid(self):
        validated, _ = self.validate(jester_exchange_count="", jester_exchange_threshold="bad")
        self.assertEqual(validated["jester_exchange_count"], 0)
        self.assertEqual(validated["jester_exchange_threshold"], 3)

        validated, _ = self.validate(jester_exchange_count="0", jester_exchange_threshold="0")
        self.assertEqual(validated["jester_exchange_count"], 0)
        self.assertEqual(validated["jester_exchange_threshold"], 3)

        validated, _ = self.validate(jester_exchange_count="4", jester_exchange_threshold="5")
        self.assertEqual(validated["jester_exchange_count"], 4)
        self.assertEqual(validated["jester_exchange_threshold"], 5)

        config = self.validate()[0]
        config.pop("jester_exchange_count")
        config.pop("jester_exchange_threshold")
        validated, _ = validate_merchant_settings(config)
        self.assertEqual(validated["jester_exchange_count"], 0)
        self.assertEqual(validated["jester_exchange_threshold"], 3)


class MerchantItemQuantityTests(unittest.TestCase):
    def validate_items(self, key, values):
        config = {
            "merchant_extra_slot": "0",
            "inventory_click_delay": "0",
            "jester_exchange_count": 0,
            "jester_exchange_threshold": "3",
            "Mari_Items": {},
            "Jester_Items": {},
            "Jester_Exchange_Items": {},
            "Rin_Items": {},
        }
        config[key] = {"Test Item": values}
        return validate_merchant_settings(config)

    def assert_quantity(self, key, raw_quantity, expected):
        validated, _ = self.validate_items(key, [True, raw_quantity, False])
        self.assertEqual(validated[key]["Test Item"][1], expected)

    def test_mari_quantities_blank_malformed_zero_and_valid(self):
        self.assert_quantity("Mari_Items", "", 1)
        self.assert_quantity("Mari_Items", "many", 1)
        self.assert_quantity("Mari_Items", "0", 1)
        self.assert_quantity("Mari_Items", "6", 6)

    def test_jester_quantities_blank_malformed_zero_and_valid(self):
        self.assert_quantity("Jester_Items", "", 1)
        self.assert_quantity("Jester_Items", None, 1)
        self.assert_quantity("Jester_Items", 0, 1)
        self.assert_quantity("Jester_Items", 3, 3)

    def test_missing_quantity_uses_one_for_mari_and_jester(self):
        for key in ("Mari_Items", "Jester_Items"):
            with self.subTest(key=key):
                validated, warnings = self.validate_items(key, [True])
                self.assertEqual(validated[key]["Test Item"][1], 1)
                self.assertTrue(any(f"{key}.Test Item.quantity" in warning for warning in warnings))

    def test_malformed_item_record_is_skipped(self):
        for key in ("Mari_Items", "Jester_Items", "Jester_Exchange_Items"):
            with self.subTest(key=key):
                validated, warnings = self.validate_items(key, None)
                self.assertNotIn("Test Item", validated[key])
                self.assertTrue(any(f"{key}.Test Item.quantity" in warning for warning in warnings))

    def test_valid_mari_jester_and_exchange_records_are_unchanged(self):
        config = {
            "merchant_extra_slot": "0",
            "inventory_click_delay": "650",
            "jester_exchange_count": 2,
            "jester_exchange_threshold": "3",
            "Mari_Items": {"Gear A": [True, 2, False]},
            "Jester_Items": {"Heavenly Potion": [True, 1, False]},
            "Jester_Exchange_Items": {"Icicle": [False, 4, False, False]},
            "Rin_Items": {},
        }
        validated, warnings = validate_merchant_settings(config)
        self.assertEqual(validated["Mari_Items"], config["Mari_Items"])
        self.assertEqual(validated["Jester_Items"], config["Jester_Items"])
        self.assertEqual(validated["Jester_Exchange_Items"], config["Jester_Exchange_Items"])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
