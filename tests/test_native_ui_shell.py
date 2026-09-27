import os

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from native_ui.app import NAVIGATION, NativeWindow


def test_native_shell_is_non_automating_during_migration():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    window = NativeWindow()
    try:
        assert len(window.nav_buttons) == sum(len(items) for _, items in NAVIGATION)
        assert window.start_button.isEnabled() is False
        assert window.nav_buttons["notice"].isEnabled() is True
        assert window.nav_buttons["fishing"].isEnabled() is False
        assert window.windowTitle().startswith("Reoteab v0.1.3")
        window.theme_select.setCurrentIndex(0)
        assert window.frame.corner_color.name() == "#7c5bf5"
        window.theme_select.setCurrentIndex(1)
        assert window.frame.corner_color.name() == "#e09f3e"
    finally:
        window.close()
