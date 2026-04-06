"""
main.py - Main Entry Point, called via CLI 'benzintracker'.
"""
import sys
from PySide6.QtWidgets import QApplication
from benzintracker.database.db import init_db
from benzintracker.ui.main_window import MainWindow
from benzintracker.translator import translator


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("BenzinTracker")
    app.setOrganizationName("benzintracker")

    # Load and set the theme before creating the main window;
    from benzintracker.settings import app_settings
    from benzintracker.ui.styles import apply_theme
    from benzintracker import config

    key = app_settings.api_key
    if key: config.API_KEY = key

    # Load Language (saved or system language);
    saved_locale = app_settings.language
    if not saved_locale: saved_locale = translator.detect_system_language()
    translator.set_language(saved_locale)

    saved_theme = app_settings.theme
    apply_theme(saved_theme)
    #app.setStyleSheet(styles.LIGHT if saved_theme == "light" else styles.DARK)

    window = MainWindow(initial_theme=saved_theme)
    window.show()

    sys.exit(app.exec())



if __name__ == "__main__":
    main()