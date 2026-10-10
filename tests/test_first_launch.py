import ast
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def class_method_names(path, class_name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return {node.name for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


class FirstLaunchTests(unittest.TestCase):
    def test_tester_build_version_uses_the_shared_beta_identity(self):
        main_source = (REPOSITORY_ROOT / "main.py").read_text(encoding="utf-8")
        version_source = (REPOSITORY_ROOT / "reoteab_version.py").read_text(encoding="utf-8")
        self.assertIn('VERSION = "1.0.0-beta.2"', version_source)
        self.assertIn('DISPLAY_NAME = f"Reoteab {DISPLAY_VERSION}"', version_source)
        self.assertIn('current_version = VERSION', main_source)
        self.assertIn('display_name = DISPLAY_NAME', main_source)

    def test_bundled_notice_matches_the_current_release(self):
        notice = (REPOSITORY_ROOT / "assets" / "noticetabcontents.txt").read_text(encoding="utf-8")
        self.assertTrue(notice.startswith("# Reoteab 1.0 Beta 2"))

    def test_updater_api_and_install_methods_are_not_exposed(self):
        api_methods = class_method_names(REPOSITORY_ROOT / "main.py", "Api")
        action_methods = class_method_names(REPOSITORY_ROOT / "biome_tracker" / "mixin_actions.py", "ActionsMixin")

        for method in ("check_for_updates", "get_update_available", "apply_update"):
            self.assertNotIn(method, api_methods)

        for method in (
            "check_for_updates",
            "download_and_apply_update",
            "_fetch_latest_release",
            "_download_and_stage_exe_update",
            "maybe_self_rename_to_canonical_exe",
        ):
            self.assertNotIn(method, action_methods)

    def test_startup_sources_do_not_include_release_api_or_update_ui(self):
        runtime_sources = (
            REPOSITORY_ROOT / "main.py",
            REPOSITORY_ROOT / "biome_tracker" / "mixin_actions.py",
            REPOSITORY_ROOT / "biome_tracker" / "mixin_gui.py",
            REPOSITORY_ROOT / "biome_tracker" / "mixin_legacy_ui_fallback.py",
        )
        for source in runtime_sources:
            self.assertNotIn("api.github.com/repos/DeeepXD/Reoteab/releases/latest", source.read_text(encoding="utf-8"))

        app_source = (REPOSITORY_ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
        other_features_source = (REPOSITORY_ROOT / "frontend" / "src" / "pages" / "OtherFeaturesPage.tsx").read_text(encoding="utf-8")
        self.assertNotIn("UpdateBanner", app_source)
        self.assertNotIn("auto_update_enabled", other_features_source)

    def test_startup_does_not_delete_existing_webview_profiles(self):
        main_source = (REPOSITORY_ROOT / "main.py").read_text(encoding="utf-8")

        self.assertIn('WebView2UserData', main_source)
        self.assertIn('Session_{time.time_ns()}', main_source)
        self.assertNotIn('shutil.rmtree(os.path.join(_wv2_user_data_base', main_source)


if __name__ == "__main__":
    unittest.main()
