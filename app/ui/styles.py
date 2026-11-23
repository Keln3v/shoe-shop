"""Оформление в соответствии с руководством по стилю: шрифт Calibri, цветовая схема."""
from PyQt5.QtGui import QColor, QFont, QPalette

from app.constants import (
    COLOR_ACCENT,
    COLOR_MAIN_BACKGROUND,
    COLOR_SECONDARY_BACKGROUND,
    FONT_FAMILY,
)

STYLESHEET = f"""
* {{ font-family: "{FONT_FAMILY}"; }}
QLabel {{ background: transparent; }}
QFrame#panel {{ background: {COLOR_SECONDARY_BACKGROUND}; border-radius: 6px; }}
QFrame#header {{ background: {COLOR_MAIN_BACKGROUND}; border-bottom: 3px solid {COLOR_ACCENT}; }}
QLabel#pageTitle {{ font-size: 22px; font-weight: bold; }}
QLabel#hint {{ color: #5c6b6a; }}
QLabel#error {{ color: #b3261e; }}
QPushButton {{
    background: {COLOR_SECONDARY_BACKGROUND}; border: 1px solid {COLOR_ACCENT};
    border-radius: 4px; padding: 7px 16px;
}}
QPushButton:hover {{ background: #bfeedb; }}
QPushButton[primary="true"] {{ background: {COLOR_ACCENT}; border: 1px solid {COLOR_ACCENT}; font-weight: bold; }}
QPushButton[primary="true"]:hover {{ background: #5fa19e; }}
QPushButton:disabled {{ background: #e6ebea; border: 1px solid #c9d2d1; color: #8a9a99; }}
QLineEdit, QComboBox {{
    border: 1px solid {COLOR_ACCENT}; border-radius: 4px; padding: 5px 8px;
    background: {COLOR_MAIN_BACKGROUND};
}}
QTableWidget {{ border: 1px solid {COLOR_ACCENT}; gridline-color: #dfe8e6; }}
QTableWidget::item:selected {{ background: {COLOR_ACCENT}; color: black; }}
QHeaderView::section {{
    background: {COLOR_SECONDARY_BACKGROUND}; border: none; border-right: 1px solid white;
    padding: 6px; font-weight: bold;
}}
QFrame#productCard {{ background: {COLOR_MAIN_BACKGROUND}; border: 1px solid {COLOR_ACCENT}; border-radius: 6px; }}
QScrollArea {{ border: none; }}
"""


def apply_style(app):
    app.setStyle("Fusion")
    app.setFont(QFont(FONT_FAMILY, 11))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLOR_MAIN_BACKGROUND))
    palette.setColor(QPalette.Base, QColor(COLOR_MAIN_BACKGROUND))
    palette.setColor(QPalette.AlternateBase, QColor(COLOR_SECONDARY_BACKGROUND))
    palette.setColor(QPalette.Text, QColor("#1b2b2a"))
    palette.setColor(QPalette.WindowText, QColor("#1b2b2a"))
    palette.setColor(QPalette.ButtonText, QColor("#1b2b2a"))
    palette.setColor(QPalette.Highlight, QColor(COLOR_ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor("black"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
