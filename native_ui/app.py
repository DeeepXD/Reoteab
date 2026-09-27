import sys
import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from native_ui.themes import THEME_NAMES, built_in_themes


ROOT = Path(__file__).resolve().parents[1]
NAVIGATION = (
    ("General", (("notice", "📋", "Notice"), ("webhook", "🔗", "Webhook"),
                 ("stats", "📊", "Stats"), ("status", "⚙️", "Status"))),
    ("Macro Settings", (("misc", "🤖", "Automated actions"),
                        ("calibrations", "🎯", "Macro Calibrations"),
                        ("presets", "▤", "Macro Presets"),
                        ("remoteaccess", "🔑", "Remote Control"))),
    ("Main Features", (("fishing", "🎣", "Fishing"), ("merchant", "🎭", "Merchant"),
                       ("autopopbuff", "🧪", "Auto Pop Buff"), ("auras", "✨", "Auras"),
                       ("movements", "🗺️", "Movements"), ("potioncraft", "🧪", "Potion Crafting"),
                       ("otherfeatures", "🔧", "Other Features"),
                       ("customization", "🔧", "Customizations"),
                       ("themedesign", "🎨", "Theme Design"))),
)


class BracketFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.corner_color = QColor("#e09f3e")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(self.corner_color, 2))
        right, bottom = self.width() - 2, self.height() - 2
        for x, dx in ((1, 18), (right, -18)):
            for y, dy in ((1, 18), (bottom, -18)):
                painter.drawLine(x, y, x + dx, y)
                painter.drawLine(x, y, x, y + dy)


class BracketButton(QPushButton):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(self.property("cornerColor") or "#e09f3e"), 1.5))
        right, bottom = self.width() - 1, self.height() - 1
        for x, dx in ((1, 10), (right, -10)):
            for y, dy in ((1, 7), (bottom, -7)):
                painter.drawLine(x, y, x + dx, y)
                painter.drawLine(x, y, x, y + dy)


class NativeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.palettes = built_in_themes()
        self.nav_buttons = {}
        self.setWindowTitle("Reoteab v0.1.3 — native UI development")
        self.resize(985, 600)
        self.setMinimumSize(650, 500)

        frame = BracketFrame()
        self.frame = frame
        self.setCentralWidget(frame)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)

        brand = QWidget()
        brand.setObjectName("brand")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(18, 20, 18, 10)
        brand_layout.setSpacing(2)
        title = QLabel("Reoteab")
        title.setObjectName("brandTitle")
        brand_layout.addWidget(title)
        version = QLabel("0.1.3")
        version.setObjectName("version")
        brand_layout.addWidget(version)
        side_layout.addWidget(brand)

        side_scroll = QScrollArea()
        side_scroll.setWidgetResizable(True)
        side_scroll.setFrameShape(QFrame.Shape.NoFrame)
        side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side_content = QWidget()
        side_items = QVBoxLayout(side_content)
        side_items.setContentsMargins(8, 8, 8, 8)
        side_items.setSpacing(4)
        for section, entries in NAVIGATION:
            heading = QLabel(section.upper())
            heading.setObjectName("section")
            side_items.addWidget(heading)
            for key, icon, label in entries:
                button = BracketButton(f"{icon}   {label}")
                button.setObjectName("navItem")
                button.setProperty("active", key == "notice")
                button.setToolTip(label if key == "notice" else f"{label} is not migrated yet")
                button.setEnabled(key == "notice")
                side_items.addWidget(button)
                self.nav_buttons[key] = button
        side_items.addStretch()
        side_scroll.setWidget(side_content)
        side_layout.addWidget(side_scroll, 1)
        footer = QLabel("Unofficial community-maintained\nproject")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(footer)
        layout.addWidget(sidebar)

        main = QWidget()
        main.setObjectName("main")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        header_layout.setSpacing(14)
        self.start_button = QPushButton("▶ Start (F1)")
        self.start_button.setObjectName("start")
        self.start_button.setEnabled(False)
        self.start_button.setToolTip("Automation is not connected in the native UI development build")
        header_layout.addWidget(self.start_button)
        status = QLabel("● Idle")
        status.setObjectName("status")
        header_layout.addWidget(status)
        header_layout.addStretch()
        for label in ("🔍 Filter index", "Import Config"):
            control = QPushButton(label)
            control.setObjectName("headerControl")
            control.setEnabled(False)
            control.setToolTip("Not connected in the native UI development build")
            header_layout.addWidget(control)
        theme_label = QLabel("Macro Theme:")
        header_layout.addWidget(theme_label)
        self.theme_select = QComboBox()
        self.theme_select.addItems(name.title() for name in THEME_NAMES)
        self.theme_select.currentIndexChanged.connect(self.apply_theme)
        header_layout.addWidget(self.theme_select)
        main_layout.addWidget(header)

        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        content_scroll.setObjectName("contentScroll")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        heading = QLabel("Notice")
        heading.setObjectName("pageTitle")
        content_layout.addWidget(heading)
        subtitle = QLabel("Latest updates and patch notes")
        subtitle.setObjectName("subtitle")
        content_layout.addWidget(subtitle)
        banner = QLabel("Reoteab is an unofficial community-maintained continuation. See the repository for current notes and releases.")
        banner.setObjectName("banner")
        banner.setWordWrap(True)
        content_layout.addWidget(banner)
        self.add_notices(content_layout)
        links = QWidget()
        links.setObjectName("banner")
        link_layout = QHBoxLayout(links)
        link_layout.setContentsMargins(16, 12, 16, 12)
        for label, url in (("Join the Reoteab Discord", "https://discord.gg/bQNSU3pfPF"),
                           ("Reoteab on GitHub", "https://github.com/DeeepXD/Reoteab")):
            link = QPushButton(label)
            link.setObjectName("link")
            link.clicked.connect(lambda checked=False, address=url: webbrowser.open(address))
            link_layout.addWidget(link)
        link_layout.addStretch()
        content_layout.addWidget(links)
        content_layout.addStretch()
        content_scroll.setWidget(content)
        main_layout.addWidget(content_scroll, 1)
        layout.addWidget(main, 1)

        self.theme_select.setCurrentIndex(1)
        self.apply_theme(1)

    def add_notices(self, layout):
        text = (ROOT / "assets" / "noticetabcontents.txt").read_text(encoding="utf-8")
        current = None
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("PLEASE WATCH"):
                continue
            if line.startswith("# "):
                current = QFrame()
                current.setObjectName("noticeCard")
                card_layout = QVBoxLayout(current)
                card_layout.setContentsMargins(20, 18, 20, 18)
                card_layout.setSpacing(8)
                label = QLabel(line[2:])
                label.setObjectName("cardTitle")
                card_layout.addWidget(label)
                layout.addWidget(current)
            elif current is not None:
                label = QLabel(("– " + line[3:]) if line.startswith("## ") else ("→ " + line[2:] if line.startswith("- ") else "→ " + line))
                if line.startswith("## "):
                    label.setObjectName("noticeSection")
                label.setWordWrap(True)
                current.layout().addWidget(label)

    def apply_theme(self, index):
        if index < 0:
            return
        theme = self.palettes[THEME_NAMES[index]]
        self.frame.corner_color = QColor(theme["--accent"])
        for card in self.findChildren(BracketFrame):
            card.corner_color = QColor(theme["--accent"])
            card.update()
        for button in self.nav_buttons.values():
            button.setProperty("cornerColor", theme["--accent"])
            button.update()
        self.setStyleSheet(f"""
            QWidget {{ color: {theme['--text-primary']}; background: transparent; }}
            QMainWindow, BracketFrame {{ background: {theme['--bg-root']}; }}
            QWidget#main {{ background: {theme['--bg-main']}; }}
            QFrame#sidebar, QFrame#header, QWidget#brand {{ background: {theme['--bg-sidebar']}; }}
            QFrame#sidebar {{ border-right: 1px solid {theme['--border']}; }}
            QFrame#header, QWidget#brand {{ border-bottom: 1px solid {theme['--border']}; }}
            QLabel#brandTitle {{ color: #a78bfa; font-size: 17px; font-weight: 800; }}
            QLabel#version, QLabel#section, QLabel#footer {{ color: {theme['--text-muted']}; }}
            QLabel#section {{ font-size: 10px; letter-spacing: 1px; padding: 14px 10px 6px; }}
            QLabel#footer {{ font-size: 10px; padding: 14px; border-top: 1px solid {theme['--border']}; }}
            QPushButton#navItem {{ text-align: left; padding: 9px 12px; border: none; background: transparent; color: {theme['--text-secondary']}; }}
            QPushButton#navItem[active="true"] {{ color: {theme['--accent-text']}; background: {theme['--bg-card']}; border-left: 3px solid {theme['--accent']}; }}
            QPushButton#start {{ background: #1aad52; color: white; border: none; padding: 7px 12px; }}
            QPushButton#start:disabled {{ color: #a1a1aa; background: {theme['--bg-input']}; }}
            QPushButton#headerControl {{ color: {theme['--text-muted']}; background: {theme['--bg-input']}; border: 1px solid {theme['--border']}; padding: 5px 10px; }}
            QLabel#status {{ color: {theme['--text-muted']}; background: {theme['--bg-input']}; border: 1px solid {theme['--border']}; border-radius: 10px; padding: 5px 12px; }}
            QComboBox {{ background: {theme['--bg-input']}; border: 1px solid {theme['--border']}; padding: 5px 10px; }}
            QLabel#pageTitle {{ font-size: 20px; font-weight: 700; }}
            QLabel#subtitle {{ color: {theme['--text-secondary']}; }}
            QLabel#banner, QWidget#banner {{ background: {theme['--bg-card']}; border: 1px solid {theme['--border-accent']}; padding: 12px; }}
            QFrame#noticeCard {{ background: {theme['--bg-sidebar']}; border-left: 3px solid {theme['--accent']}; }}
            QLabel#cardTitle {{ color: {theme['--accent-text']}; font-size: 14px; font-weight: 600; }}
            QLabel#noticeSection {{ font-weight: 600; }}
            QPushButton#link {{ color: {theme['--accent-text']}; background: transparent; border: none; text-decoration: underline; }}
            QScrollArea, QScrollArea > QWidget > QWidget {{ border: none; background: transparent; }}
        """)
        self.frame.update()


def main():
    app = QApplication(sys.argv)
    fonts = ROOT / "frontend" / "public" / "fonts"
    QFontDatabase.addApplicationFont(str(fonts / "sarpanch-400.ttf"))
    QFontDatabase.addApplicationFont(str(fonts / "sarpanch-700.ttf"))
    app.setFont(QFont("Sarpanch", 10))
    window = NativeWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
