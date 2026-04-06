"""
styles.py - Stylesheets for Benzintracker.

Light and Dark stylesheets for the whole application.
It's being applied at start and the theme-toggle.
"""

LIGHT = """
    QMainWindow, QWidget {
        background-color: #f5f5f5;
        color: #1a1a1a;
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }

    QTabWidget::pane {
        border: 1px solid #d0d0d0;
        background: #ffffff;
        border-radius: 4px;
    }

    QTabBar::tab {
        background: #e0e0e0;
        color: #444;
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }

    QTabBar::tab:selected {
        background: #ffffff;
        color: #1a1a1a;
        font-weight: bold;
        border-bottom: 2px solid #2196F3;
    }

    QTabBar::tab:hover:!selected { background: #ebebeb; }

    QTableWidget {
        background: #ffffff;
        alternate-background-color: #f9f9f9;
        gridline-color: #e0e0e0;
        border: 1px solid #d0d0d0;
    }

    QHeaderView::section {
        background: #eeeeee;
        color: #333;
        padding: 6px;
        border: none;
        border-right: 1px solid #d0d0d0;
        font-weight: bold;
    }

    QPushButton {
        background-color: #2196F3;
        color: white;
        border: none;
        padding: 7px 16px;
        border-radius: 4px;
        font-weight: bold;
    }

    QPushButton:hover { background-color: #1e88e5; }
    QPushButton:pressed { background-color: #1565c0; }
    QPushButton:disabled {background-color: #bdbdbd; color: #757575; }

    QPushButton#btn_secondary {
        background-color: transparent;
        color: #2196F3;
        border: 1px solid #2196F3;
    }
    QPushButton#btn_secondary:hover { background-color: #e3f2fd; }

    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background: #ffffff;
        border: 1px solid #bdbdbd;
        border-radius: 4px;
        padding: 5px 8px;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #2196F3; }

    QLabel#label_status { color: #555; font-size: 11px; }
    QLabel#label_error { color: #e53935; font-size: 11px; }

    QStatusBar {
        background: #eeeeee;
        color: #555;
        font-size: 11px;
    }

    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 18px;
        border-left: 1px solid #bdbdbd;
        border-bottom: 1px solid #bdbdbd;
        border-top-right-radius: 4px;
        background: #f0f0f0;
    }
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 18px;
        border-left: 1px solid #bdbdbd;
        border-top: 1px solid #bdbdbd;
        border-bottom-right-radius: 4px;
        background: #f0f0f0;
    }
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
        background: #e0e0e0;
    }
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        image: none;
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid #555;
    }
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        image: none;
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #555;
    }
"""

DARK = """
    QMainWindow, QWidget {
        background-color: #1e1e1e;
        color: #e0e0e0;
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }
 
    QTabWidget::pane {
        border: 1px solid #3a3a3a;
        background: #252525;
        border-radius: 4px;
    }
    QTabBar::tab {
        background: #2d2d2d;
        color: #aaa;
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    QTabBar::tab:selected {
        background: #252525;
        color: #e0e0e0;
        font-weight: bold;
        border-bottom: 2px solid #42a5f5;
    }
    QTabBar::tab:hover:!selected { background: #333333; }
 
    QTableWidget {
        background: #252525;
        alternate-background-color: #2a2a2a;
        gridline-color: #3a3a3a;
        border: 1px solid #3a3a3a;
        color: #e0e0e0;
    }
    QHeaderView::section {
        background: #2d2d2d;
        color: #bbb;
        padding: 6px;
        border: none;
        border-right: 1px solid #3a3a3a;
        font-weight: bold;
    }
 
    QPushButton {
        background-color: #1976d2;
        color: white;
        border: none;
        padding: 7px 16px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover    { background-color: #1e88e5; }
    QPushButton:pressed  { background-color: #0d47a1; }
    QPushButton:disabled { background-color: #424242; color: #757575; }
 
    QPushButton#btn_secondary {
        background-color: transparent;
        color: #42a5f5;
        border: 1px solid #42a5f5;
    }
    QPushButton#btn_secondary:hover { background-color: #1a2e45; }
 
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        background: #2d2d2d;
        border: 1px solid #4a4a4a;
        border-radius: 4px;
        padding: 5px 8px;
        color: #e0e0e0;
    }
    QLineEdit:focus, QComboBox:focus,
    QSpinBox:focus, QDoubleSpinBox:focus { border-color: #42a5f5; }
 
    QLabel#label_status { color: #aaa; font-size: 11px; }
    QLabel#label_error  { color: #ef5350; font-size: 11px; }
 
    QStatusBar { background: #252525; color: #aaa; font-size: 11px; }

    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 18px;
        border-left: 1px solid #4a4a4a;
        border-bottom: 1px solid #4a4a4a;
        border-top-right-radius: 4px;
        background: #3a3a3a;
    }
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 18px;
        border-left: 1px solid #4a4a4a;
        border-top: 1px solid #4a4a4a;
        border-bottom-right-radius: 4px;
        background: #3a3a3a;
    }
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
        background: #444;
    }
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        image: none;
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid #ccc;
    }
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        image: none;
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #ccc;
    }
"""