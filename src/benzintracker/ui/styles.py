"""
styles.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: Stylesheets for Benzintracker.
=========================================================================================

Native Styling via QApplication.setStyle("fusion") + QPalette.

Fusion is a Qt-nativ, cross-platform consistent and supports QPalette completely.
The Stylesheet only touches classes outside of QPalette (Error and status labels).
"""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


_LIGHT = {
    "window":          "#f5f5f5",
    "window_text":     "#1a1a1a",
    "base":            "#ffffff",
    "alt_base":        "#f0f0f0",
    "text":            "#1a1a1a",
    "button":          "#e0e0e0",
    "button_text":     "#1a1a1a",
    "highlight":       "#2196F3",
    "highlight_text":  "#ffffff",
    "link":            "#1976d2",
    "mid":             "#c0c0c0",
    "midlight":        "#e8e8e8",
    "dark":            "#a0a0a0",
    "shadow":          "#787878",
    "tooltip_base":    "#fffde7",
    "tooltip_text":    "#1a1a1a",
    "placeholder":     "#9e9e9e",
    "status_text":     "#666666"
}
 
_DARK = {
    "window":          "#1e1e1e",
    "window_text":     "#e0e0e0",
    "base":            "#252525",
    "alt_base":        "#2a2a2a",
    "text":            "#e0e0e0",
    "button":          "#2d2d2d",
    "button_text":     "#e0e0e0",
    "highlight":       "#1976d2",
    "highlight_text":  "#ffffff",
    "link":            "#42a5f5",
    "mid":             "#3a3a3a",
    "midlight":        "#333333",
    "dark":            "#141414",
    "shadow":          "#0a0a0a",
    "tooltip_base":    "#2d2d2d",
    "tooltip_text":    "#e0e0e0",
    "placeholder":     "#757575",
    "status_text":     "#9e9e9e"
}


def _build_palette(tokens: dict) -> QPalette:
    p = QPalette()

    p.setColor(QPalette.ColorRole.Window,           QColor(tokens["window"]))
    p.setColor(QPalette.ColorRole.WindowText,       QColor(tokens["window_text"]))
    p.setColor(QPalette.ColorRole.Base,             QColor(tokens["base"]))
    p.setColor(QPalette.ColorRole.AlternateBase,    QColor(tokens["alt_base"]))
    p.setColor(QPalette.ColorRole.Text,             QColor(tokens["text"]))
    p.setColor(QPalette.ColorRole.Button,           QColor(tokens["button"]))
    p.setColor(QPalette.ColorRole.ButtonText,       QColor(tokens["button_text"]))
    p.setColor(QPalette.ColorRole.Highlight,        QColor(tokens["highlight"]))
    p.setColor(QPalette.ColorRole.HighlightedText,  QColor(tokens["highlight_text"]))
    p.setColor(QPalette.ColorRole.Link,             QColor(tokens["link"]))
    p.setColor(QPalette.ColorRole.Mid,              QColor(tokens["mid"]))
    p.setColor(QPalette.ColorRole.Midlight,         QColor(tokens["midlight"]))
    p.setColor(QPalette.ColorRole.Dark,             QColor(tokens["dark"]))
    p.setColor(QPalette.ColorRole.Shadow,           QColor(tokens["shadow"]))
    p.setColor(QPalette.ColorRole.ToolTipBase,      QColor(tokens["tooltip_base"]))
    p.setColor(QPalette.ColorRole.ToolTipText,      QColor(tokens["tooltip_text"]))
    p.setColor(QPalette.ColorRole.PlaceholderText,  QColor(tokens["placeholder"]))

    # Disabled group: dimmed variants;
    disabled_color = QColor(tokens["status_text"])
    for role in [
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ]:
        p.setColor(QPalette.ColorGroup.Disabled, role, disabled_color)

    return p


PALETTE_LIGHT = _build_palette(_LIGHT)
PALETTE_DARK = _build_palette(_DARK)

# Minimal stylesheet for semantic classes which QPalette does not cover;
def _semantic_stylesheet(status_color: str) -> str:
    return f"""
    QLabel#label_error       {{ color: #e53935; font-size: 11px; }}
    QLabel#label_status      {{ color: {status_color}; font-size: 11px; }}
    QToolBar                 {{ border: none; padding: 4px 8px; spacing: 8px; }}
    QStatusBar               {{ font-size: 11px; color: {status_color}; }}
"""


def apply_theme(theme: str):
    """
    Apply fusion style + QPalette + minimal stylesheet.
    Must be called AFTER QApplication creation.

    Args:
        theme: "light" or "dark"
    """
    tokens = _LIGHT if theme == "light" else _DARK
    palette = _build_palette(tokens)

    app = QApplication.instance()
    app.setStyle("fusion")
    app.setPalette(palette)
    app.setStyleSheet(_semantic_stylesheet(tokens["status_text"]))