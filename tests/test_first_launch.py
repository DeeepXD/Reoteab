import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import requests

from biome_tracker.mixin_actions import ActionsMixin


class FirstLaunchTests(unittest.TestCase):
    def setUp(self):
        self.actions = ActionsMixin()

    def test_release_comparison_does_not_downgrade_hotfix(self):
        self.assertFalse(self.actions._is_newer_version("v2.2.0", "v2.2.0-hotfix1"))
        self.assertFalse(self.actions._is_newer_version("v2.1.9", "v2.2.0-hotfix1"))
        self.assertTrue(self.actions._is_newer_version("v2.2.0-hotfix2", "v2.2.0-hotfix1"))
        self.assertTrue(self.actions._is_newer_version("v2.2.1", "v2.2.0-hotfix1"))

    def test_release_comparison_orders_beta_prereleases(self):
        self.assertFalse(self.actions._is_newer_version("v0.1.0-beta.4", "v0.1.0-beta.5"))
        self.assertTrue(self.actions._is_newer_version("v0.1.0-beta.6", "v0.1.0-beta.5"))
        self.assertTrue(self.actions._is_newer_version("v0.1.0", "v0.1.0-beta.5"))
        self.assertFalse(self.actions._is_newer_version("v0.1.0", "0.1.0"))

    def test_missing_latest_release_is_ignored(self):
        response = mock.Mock()
        response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        with mock.patch("biome_tracker.mixin_actions.requests.get", return_value=response):
            self.assertIsNone(self.actions._fetch_latest_release())

    def test_update_check_ignores_older_release(self):
        release = {
            "tag_name": "v0.1.0-beta.4",
            "assets": [{"name": "Reoteab.exe", "browser_download_url": "https://example.invalid/Reoteab.exe"}],
        }
        with (
            mock.patch.object(self.actions, "_fetch_latest_release", return_value=release),
            mock.patch.object(self.actions, "_download_and_stage_exe_update") as download,
        ):
            self.actions.on_update_available = mock.Mock()
            self.actions.check_for_updates()
        download.assert_not_called()
        self.actions.on_update_available.assert_not_called()

    def test_update_check_ignores_matching_v010_release(self):
        release = {
            "tag_name": "v0.1.0",
            "assets": [{"name": "Reoteab.exe", "browser_download_url": "https://example.invalid/Reoteab.exe"}],
        }
        with (
            mock.patch.object(self.actions, "_fetch_latest_release", return_value=release),
            mock.patch.object(self.actions, "_download_and_stage_exe_update") as download,
        ):
            self.actions.on_update_available = mock.Mock()
            self.actions.check_for_updates()
        download.assert_not_called()
        self.actions.on_update_available.assert_not_called()

    def test_update_check_notifies_without_installing(self):
        release = {
            "tag_name": "v0.1.1",
            "assets": [{"name": "Reoteab.exe", "browser_download_url": "https://example.invalid/Reoteab.exe"}],
        }
        with (
            mock.patch.object(self.actions, "_fetch_latest_release", return_value=release),
            mock.patch.object(self.actions, "_download_and_stage_exe_update") as download,
            mock.patch.object(self.actions, "_spawn_detached_exe") as spawn,
        ):
            self.actions.on_update_available = mock.Mock()
            self.actions.check_for_updates()
        self.actions.on_update_available.assert_called_once_with("v0.1.1", "https://example.invalid/Reoteab.exe")
        download.assert_not_called()
        spawn.assert_not_called()

    def test_explicit_update_approval_starts_installation(self):
        self.actions.on_update_status = mock.Mock()
        with (
            mock.patch.object(sys, "frozen", True, create=True),
            mock.patch.object(self.actions, "_download_and_stage_exe_update", return_value=True) as download,
            mock.patch("biome_tracker.mixin_actions.time.sleep"),
            mock.patch("biome_tracker.mixin_actions.os._exit") as exit_process,
        ):
            self.actions.download_and_apply_update("https://example.invalid/Reoteab.exe", version="v0.1.1")
        download.assert_called_once_with("https://example.invalid/Reoteab.exe", asset_name="Reoteab.exe")
        exit_process.assert_called_once_with(0)

    def test_normal_renamed_executable_is_not_copied_or_relaunched(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / "Reoteab.exe")
            with (
                mock.patch.object(sys, "frozen", True, create=True),
                mock.patch.object(sys, "executable", executable),
                mock.patch.object(sys, "argv", [executable]),
                mock.patch("biome_tracker.mixin_actions.shutil.copy2") as copy_exe,
                mock.patch.object(self.actions, "_spawn_detached_exe") as spawn,
            ):
                self.assertFalse(self.actions.maybe_self_rename_to_canonical_exe())
            copy_exe.assert_not_called()
            spawn.assert_not_called()

    def test_updater_payload_still_finalizes_to_canonical_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            current_exe = Path(directory) / "Reoteab-update.exe"
            canonical_exe = Path(directory) / "Reoteab.exe"
            current_exe.write_bytes(b"updated executable")
            with (
                mock.patch.object(sys, "frozen", True, create=True),
                mock.patch.object(sys, "executable", str(current_exe)),
                mock.patch.object(sys, "argv", [str(current_exe), "--coteab-finalize-update"]),
                mock.patch.object(self.actions, "_spawn_detached_exe", return_value=True) as spawn,
            ):
                self.assertTrue(self.actions.maybe_self_rename_to_canonical_exe())
            self.assertEqual(canonical_exe.read_bytes(), b"updated executable")
            spawn.assert_called_once_with(str(canonical_exe))


if __name__ == "__main__":
    unittest.main()
