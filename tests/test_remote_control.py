import asyncio
import builtins
import queue
import unittest
from unittest import mock

from biome_tracker.mixin_remote import RemoteMixin


class _Value:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class _RemoteHarness(RemoteMixin):
    def __init__(self, enabled=True):
        self.config = {}
        self.remote_access_var = _Value(enabled)
        self.remote_bot_token_var = _Value("test-token")
        self.remote_allowed_user_id_var = _Value("")
        self.remote_command_queue = queue.Queue()
        self.remote_worker_running = False
        self.remote_bot_thread = None
        self.remote_bot_obj = None
        self.saved = False

    def save_config(self):
        self.saved = True

    def set_title_threadsafe(self, title):
        pass

    def error_logging(self, error, context):
        raise AssertionError(f"{context}: {error}")


class _Context:
    def __init__(self):
        self.responses = []

    async def respond(self, *args, **kwargs):
        self.responses.append((args, kwargs))


class RemoteControlTests(unittest.TestCase):
    def test_discord_imports_with_audioop_dependency(self):
        import audioop
        import discord

        self.assertIsNotNone(audioop)
        self.assertTrue(hasattr(discord, "Bot"))

    def test_disabled_remote_control_does_not_import_discord(self):
        harness = _RemoteHarness(enabled=False)
        imported = []
        original_import = builtins.__import__

        def recording_import(name, *args, **kwargs):
            imported.append(name)
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=recording_import):
            harness._remote_access_toggle()

        self.assertFalse(any(name == "discord" or name.startswith("discord.") for name in imported))
        self.assertTrue(harness.saved)

    def test_enabled_bot_initializes_and_commands_dispatch(self):
        import discord

        harness = _RemoteHarness(enabled=True)
        captured = {}

        def fake_run(bot, token):
            captured["bot"] = bot
            captured["token"] = token

        with mock.patch.object(discord.Bot, "run", fake_run):
            harness._remote_bot_thread_func()

        self.assertEqual(captured["token"], "test-token")
        commands = {command.name: command for command in captured["bot"].pending_application_commands}
        self.assertEqual(
            set(commands),
            {
                "start", "stop", "status", "close_roblox_and_stop_macro",
                "equip_aura", "rejoin", "help", "use", "check_merchant",
                "screenshot", "reroll_quest",
            },
        )

        started = []
        harness.on_remote_start = lambda: started.append(True)
        context = _Context()
        asyncio.run(commands["start"].callback(context))
        self.assertEqual(started, [True])
        self.assertEqual(len(context.responses), 1)


if __name__ == "__main__":
    unittest.main()
