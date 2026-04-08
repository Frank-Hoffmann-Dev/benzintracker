"""
main.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: Main Entry Point, called via CLI 'benzintracker'.
=========================================================================================

The order of loading is CRITICAL:
    1. QApplication()               -> Must exists BEFORE QSettings
    2. read app_settings            -> Now QSettings is actually usable
    3. Set DB-Path into config      -> Must be set BEFORE init_db()
    4. init_db()                    -> open the db from the set path
    5. Lang + Theme                 -> prepare for GUI
    6. MainWindow()
"""
import os
import sys


def main():
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("BenzinTracker")
    app.setOrganizationName("benzintracker")

    # Load and set the theme before creating the main window;
    from benzintracker.settings import app_settings
    from benzintracker.ui.styles import apply_theme
    from benzintracker.translator import translator
    from benzintracker import config
    from benzintracker.database.db import init_db

    saved_db_path = app_settings.db_path
    if saved_db_path:
        db_dir = os.path.dirname(saved_db_path)
        if db_dir: os.makedirs(db_dir, exist_ok=True)
        config.DB_PATH = saved_db_path

    init_db()

    key = app_settings.api_key
    if key: config.API_KEY = key

    # Load Language (saved or system language);
    saved_locale = app_settings.language
    if not saved_locale: saved_locale = translator.detect_system_language()
    translator.set_language(saved_locale)

    saved_theme = app_settings.theme
    apply_theme(saved_theme)

    from benzintracker.ui.main_window import MainWindow
    window = MainWindow(initial_theme=saved_theme)
    window.show()

    sys.exit(app.exec())



if __name__ == "__main__":
    main()