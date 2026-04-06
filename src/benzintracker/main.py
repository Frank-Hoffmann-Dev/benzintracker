"""
main.py - Main Entry Point, called via CLI 'benzintracker'.
"""
import sys
from PySide6.QtWidgets import QApplication
from benzintracker.database.db import init_db
from benzintracker.ui.main_window import MainWindow


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("BenzinTracker")
    app.setOrganizationName("benzintracker")

    # Load and set the theme before creating the main window;
    from benzintracker.settings import app_settings
    from benzintracker.ui import styles
    from benzintracker import config

    key = app_settings.api_key
    if key: config.API_KEY = key

    saved_theme = app_settings.theme
    app.setStyleSheet(styles.LIGHT if saved_theme == "light" else styles.DARK)

    window = MainWindow(initial_theme=saved_theme)
    window.show()

    sys.exit(app.exec())



if __name__ == "__main__":
    main()