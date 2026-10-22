"""Tema visual: estilo Fusion com paleta escura e alguns ajustes via QSS."""

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

BG = "#15171c"
PANEL = "#1d2027"
FIELD = "#262a33"
BORDER = "#323743"
TEXT = "#e6e8ec"
MUTED = "#9aa3b2"
DISABLED = "#5c6370"
ACCENT = "#4c8dff"
ACCENT_SOFT = "#28406b"
ERROR = "#ff6b6b"
VIEWER_BG = "#101216"

STYLE = f"""
QFrame#Panel {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#Panel QLabel {{ background: transparent; }}
QLabel#PanelTitle {{ font-size: 11pt; font-weight: 600; }}
QLabel#Muted {{ color: {MUTED}; }}
QLabel#Error {{ color: {ERROR}; }}
QLabel#InfoBox, QFrame#InfoCard {{
    background: {FIELD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px;
}}
QLabel#InfoBox {{ font-family: Consolas, monospace; }}
QPlainTextEdit#Code {{
    background: {VIEWER_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    font-family: Consolas, monospace;
    font-size: 9pt;
    color: #c8d3f5;
}}
QTreeWidget, QListWidget, QLineEdit {{
    background: {FIELD};
    border: 1px solid {BORDER};
    border-radius: 6px;
}}
QLineEdit {{ padding: 5px 8px; }}
QTreeWidget::item {{ padding: 3px 2px; }}
QTreeWidget::item:selected, QListWidget::item:selected {{
    background: {ACCENT_SOFT};
    color: white;
    border-radius: 4px;
}}
QPushButton {{
    background: {FIELD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:disabled {{ color: {DISABLED}; border-color: {BORDER}; }}
QPushButton#Primary {{
    background: {ACCENT};
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton#Primary:disabled {{ background: {ACCENT_SOFT}; color: {MUTED}; }}
QToolBar {{
    background: {PANEL};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 4px 8px;
    spacing: 4px;
}}
QToolBar QToolButton {{ padding: 6px 10px; border-radius: 6px; }}
QToolBar QToolButton:hover {{ background: {FIELD}; }}
QStatusBar {{
    background: {PANEL};
    border-top: 1px solid {BORDER};
    color: {MUTED};
}}
QStatusBar QLabel {{ color: {MUTED}; padding: 0 8px; }}
QSplitter::handle {{ background: {BG}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
"""


def apply_theme(app: QApplication):
    app.setStyle("Fusion")
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: BG,
        QPalette.ColorRole.WindowText: TEXT,
        QPalette.ColorRole.Base: FIELD,
        QPalette.ColorRole.AlternateBase: PANEL,
        QPalette.ColorRole.ToolTipBase: PANEL,
        QPalette.ColorRole.ToolTipText: TEXT,
        QPalette.ColorRole.Text: TEXT,
        QPalette.ColorRole.Button: FIELD,
        QPalette.ColorRole.ButtonText: TEXT,
        QPalette.ColorRole.BrightText: "#ffffff",
        QPalette.ColorRole.Highlight: ACCENT,
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.Link: ACCENT,
        QPalette.ColorRole.PlaceholderText: MUTED,
        QPalette.ColorRole.Mid: BORDER,
        QPalette.ColorRole.Dark: BG,
    }
    for role, color in roles.items():
        palette.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(DISABLED))
    app.setPalette(palette)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(STYLE)
