import importlib.util
from pathlib import Path


def load_config_module(name: str):
    path = Path(__file__).parents[1] / "biome_tracker" / "config.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_runtime_root_override_never_imports_legacy_config(monkeypatch, tmp_path):
    local_appdata = tmp_path / "local"
    legacy = local_appdata / "CoteabMacro"
    legacy.mkdir(parents=True)
    (legacy / "config.json").write_text('{"webhook_url": ["private"]}', encoding="utf-8")
    runtime = tmp_path / "Reoteab-DevLab"

    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))
    monkeypatch.setenv("REOTEAB_RUNTIME_ROOT", str(runtime))
    config = load_config_module("devlab_config_test")
    config.ensure_workspace_files()

    assert config.APPDATA_BASE == runtime
    assert "private" not in str(config.load_config())
    assert (legacy / "config.json").read_text(encoding="utf-8") == '{"webhook_url": ["private"]}'
