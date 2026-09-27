import re
from pathlib import Path


THEME_NAMES = (
    "midnight", "solar", "arctic", "neon", "sunset", "ocean",
    "forest", "cyberpunk", "lavender",
)

CSS_PATH = Path(__file__).resolve().parents[1] / "frontend" / "src" / "App.css"


def built_in_themes(css_text=None):
    if css_text is None:
        css_text = CSS_PATH.read_text(encoding="utf-8")

    themes = {}
    for name in THEME_NAMES:
        selector = r":root,\s*\[data-theme=\"midnight\"\]" if name == "midnight" else rf"\[data-theme=\"{name}\"\]"
        match = re.search(selector + r"\s*\{([^}]*)\}", css_text)
        if not match:
            raise ValueError(f"Missing {name} theme in App.css")
        themes[name] = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", match.group(1)))

    base = themes["midnight"]
    return {name: {**base, **values} for name, values in themes.items()}
