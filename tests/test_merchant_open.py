import unittest
from unittest import mock

from biome_tracker.mixin_actions import ActionsMixin


class MerchantOpenTests(unittest.TestCase):
    def test_mari_open_uses_saved_coordinate_once(self):
        actions = ActionsMixin()
        actions._fishing_br_sc_override = True
        actions.detection_running = True
        actions.reconnecting_state = False
        actions.config = {
            "merchant_name_ocr_pos": [0, 0, 1, 1],
            "merchant_open_button": [651, 943],
            "merchant_dialogue_box": [768, 836],
            "item_name_ocr_pos": [0, 0, 1, 1],
            "merchant_extra_slot": 0,
            "inventory_click_delay": 0,
            "jester_exchange_count": 0,
            "jester_exchange_threshold": 3,
            "Mari_Items": {},
            "Jester_Items": {},
            "Jester_Exchange_Items": {},
            "Rin_Items": {},
        }
        actions.append_log = mock.Mock()
        actions.save_config = mock.Mock()
        actions.extract_text_with_easyocr = mock.Mock(return_value="Mari")

        opened = False

        def sleep_with_cancel(_seconds):
            return not opened

        def mouse_click(_button, x, y, clicks=1, **_kwargs):
            nonlocal opened
            if (x, y) == (651, 943):
                opened = True

        actions._sleep_with_cancel = sleep_with_cancel
        with (
            mock.patch("biome_tracker.mixin_actions.autoit.send"),
            mock.patch("biome_tracker.mixin_actions.autoit.mouse_click", side_effect=mouse_click) as click,
            mock.patch("biome_tracker.mixin_actions.pyautogui.screenshot"),
        ):
            self.assertFalse(actions.Merchant_Handler())

        open_calls = [
            call for call in click.call_args_list
            if call.args[1:3] == (651, 943)
        ]
        self.assertEqual(len(open_calls), 1)
        self.assertEqual(open_calls[0].args[3], 1)


if __name__ == "__main__":
    unittest.main()
