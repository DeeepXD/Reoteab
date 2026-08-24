import json
import os
import tempfile
import unittest
from unittest import mock

from biome_tracker.mixin_webhook import WebhookMixin


class _Response:
    status_code = 204

    def raise_for_status(self):
        return None


class WebhookCustomizationTests(unittest.TestCase):
    def setUp(self):
        self.webhooks = WebhookMixin()
        self.webhooks.append_log = mock.Mock()

    def _post_embed(self):
        return self.post.call_args.kwargs["json"]["embeds"][0]

    def test_missing_override_keeps_merchant_default(self):
        self.webhooks.config = {
            "webhook_url": "https://example.test/webhook",
            "private_server_link": "https://server.test",
        }
        with mock.patch("biome_tracker.mixin_webhook.requests.post", return_value=_Response()) as self.post:
            self.webhooks.send_merchant_webhook("Mari")

        embed = self._post_embed()
        self.assertNotIn("title", embed)
        self.assertEqual(embed["color"], 11753)
        self.assertEqual(embed["thumbnail"]["url"], "https://i.postimg.cc/RZh2pw0j/mari.png ")
        self.assertEqual(embed["footer"]["text"], "Reoteab 0.1.0")
        self.assertIn("Mari has arrived", embed["description"])
        self.assertEqual(embed["fields"], [{"name": "Detection Source", "value": "OCR"}])
        self.assertEqual(self.post.call_count, 1)

    def test_merchant_override_keeps_ping_and_screenshot(self):
        self.webhooks.config = {
            "webhook_url": "https://example.test/webhook",
            "private_server_link": "https://server.test",
            "ping_mari": True,
            "mari_user_id": "123",
            "webhook_embed_overrides": {
                "merchant": {
                    "color": "#010203",
                    "title": "Merchant detected",
                    "footer_text": "Custom footer",
                    "footer_icon_url": "https://example.test/footer.png",
                    "thumbnail_url": "https://example.test/merchant.png",
                }
            },
        }
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as screenshot:
            screenshot.write(b"image")
            screenshot_path = screenshot.name
        try:
            with mock.patch("biome_tracker.mixin_webhook.requests.post", return_value=_Response()) as self.post:
                self.webhooks.send_merchant_webhook("Mari", screenshot_path=screenshot_path)
        finally:
            os.unlink(screenshot_path)

        payload = json.loads(self.post.call_args.kwargs["data"]["payload_json"])
        embed = payload["embeds"][0]
        self.assertEqual(payload["content"], "<@123>")
        self.assertEqual(embed["color"], 0x010203)
        self.assertEqual(embed["title"], "Merchant detected")
        self.assertEqual(embed["footer"], {
            "text": "Custom footer",
            "icon_url": "https://example.test/footer.png",
        })
        self.assertEqual(embed["thumbnail"], {"url": "https://example.test/merchant.png"})
        self.assertEqual(embed["image"]["url"], f"attachment://{os.path.basename(screenshot_path)}")
        self.assertIn("Mari has arrived", embed["description"])
        self.assertEqual(self.post.call_count, 1)

    def test_aura_override_keeps_ping_and_generated_description(self):
        self.webhooks.config = {
            "webhook_url": "https://example.test/webhook",
            "ping_minimum": "100",
            "aura_user_id": "456",
            "webhook_embed_overrides": {
                "aura": {
                    "color": "0x112233",
                    "title": "Aura detected",
                    "footer_text": "Custom footer",
                    "thumbnail_url": "https://example.test/aura.png",
                }
            },
        }
        with mock.patch("biome_tracker.mixin_webhook.requests.post", return_value=_Response()) as self.post:
            self.webhooks.send_aura_webhook("Lunar", "1,000,000", "during WINDY")

        payload = self.post.call_args.kwargs["json"]
        embed = payload["embeds"][0]
        self.assertEqual(payload["content"], "<@456>")
        self.assertEqual(embed["color"], 0x112233)
        self.assertEqual(embed["title"], "Aura detected")
        self.assertEqual(embed["footer"]["text"], "Custom footer")
        self.assertEqual(embed["thumbnail"], {"url": "https://example.test/aura.png"})
        self.assertIn("Aura equipped: Lunar | 1 in 1,000,000 during WINDY", embed["description"])
        self.assertEqual(self.post.call_count, 1)

    def test_invalid_override_values_keep_defaults(self):
        self.webhooks.config = {
            "webhook_url": "https://example.test/webhook",
            "private_server_link": "https://server.test",
            "webhook_embed_overrides": {
                "merchant": {
                    "color": "not-a-color",
                    "title": "",
                    "footer_text": None,
                    "footer_icon_url": "not a URL",
                    "thumbnail_url": "file:///local.png",
                },
                "aura": {"color": "#bad", "thumbnail_url": "../local.png"},
            },
        }
        with mock.patch("biome_tracker.mixin_webhook.requests.post", return_value=_Response()) as self.post:
            self.webhooks.send_merchant_webhook("Mari")

        embed = self._post_embed()
        self.assertNotIn("title", embed)
        self.assertEqual(embed["color"], 11753)
        self.assertEqual(embed["thumbnail"]["url"], "https://i.postimg.cc/RZh2pw0j/mari.png ")
        self.assertEqual(
            embed["footer"]["icon_url"],
            "https://raw.githubusercontent.com/DeeepXD/Reoteab/main/assets/reoteab-icon.png",
        )

        self.post.reset_mock()
        self.webhooks.send_aura_webhook("Lunar", "1,000,000", "during WINDY")
        embed = self._post_embed()
        self.assertEqual(embed["color"], 0xFF73EC)
        self.assertEqual(embed["title"], "⭐ Aura Detection ⭐")
        self.assertNotIn("thumbnail", embed)
        self.assertEqual(self.post.call_count, 1)


if __name__ == "__main__":
    unittest.main()
