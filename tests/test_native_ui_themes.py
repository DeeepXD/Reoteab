from native_ui.themes import CSS_PATH, THEME_NAMES, built_in_themes


def test_builtin_palettes_match_react_css():
    themes = built_in_themes()
    assert set(themes) == set(THEME_NAMES)
    assert themes["solar"]["--accent"] == "#e09f3e"
    assert themes["midnight"]["--bg-root"] == "#09090b"
    for theme in themes.values():
        assert all(theme[key].startswith("#") for key in (
            "--bg-root", "--bg-sidebar", "--bg-main", "--bg-card", "--accent"
        ))


def test_missing_theme_fails_visibly():
    css = CSS_PATH.read_text(encoding="utf-8")
    try:
        built_in_themes(css.replace('[data-theme="solar"]', '[data-theme="missing"]'))
    except ValueError as exc:
        assert "solar" in str(exc)
    else:
        raise AssertionError("Missing theme must not silently use another palette")
