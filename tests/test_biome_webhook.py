import unittest
from unittest import mock

from biome_tracker.mixin_webhook import WebhookMixin


class _WebhookTracker(WebhookMixin):
    def __init__(self):
        self.config = {
            "webhook_url": "https://discord.invalid/webhook",
            "private_server_link": "https://www.roblox.com/share?code=test&type=Server",
            "biome_pings": {},
        }
        self.biome_data = {
            "CYBERSPACE": {"color": "0x0A1A3D", "thumbnail_url": "https://example.invalid/cyberspace.png"},
            "GLITCHED": {"color": "0xBFFF00", "thumbnail_url": "https://example.invalid/glitched.png"},
        }
        self.append_log = mock.Mock()


class BiomeWebhookTests(unittest.TestCase):
    def setUp(self):
        self.tracker = _WebhookTracker()
        self.response = mock.Mock()

    def test_cyberspace_start_sends_only_to_configured_discord_webhook(self):
        with (
            mock.patch("biome_tracker.mixin_webhook.requests.post", return_value=self.response) as post,
            mock.patch("biome_tracker.mixin_webhook.time.sleep") as sleep,
        ):
            self.tracker.send_webhook("CYBERSPACE", "Ping", "start")

        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], "https://discord.invalid/webhook")
        self.assertIn(
            self.tracker.config["private_server_link"],
            post.call_args.kwargs["json"]["embeds"][0]["description"],
        )
        self.response.raise_for_status.assert_called_once()
        sleep.assert_not_called()

    def test_normal_biome_start_and_end_still_send(self):
        with mock.patch("biome_tracker.mixin_webhook.requests.post", return_value=self.response) as post:
            self.tracker.send_webhook("GLITCHED", "Ping", "start")
            self.tracker.send_webhook("GLITCHED", "Ping", "end")

        self.assertEqual(post.call_count, 2)
        self.assertEqual(
            [call.args[0] for call in post.call_args_list],
            ["https://discord.invalid/webhook", "https://discord.invalid/webhook"],
        )


if __name__ == "__main__":
    unittest.main()
