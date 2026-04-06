"""
main_window.py - Main Window of the Application.

Responsible for:
    - Tab-Structure (Map, Price-table, statistics, Settings)
    - QTimer for the automatic refresh
    - Theme Handling (Light / Dark)
    - Statusbar wit the last API-Call timestamp and timer for next refresh
    - Error messages
"""
from datetime import datetime
import random

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar,
    QLabel, QPushButton, QToolBar
)
from PySide6.QtCore import QTimer

from benzintracker.__init__ import __version__
from benzintracker.ui.styles import apply_theme
from benzintracker.ui.tabs.map_tab import MapTab
from benzintracker.ui.tabs.table_tab import TableTab
from benzintracker.ui.tabs.stats_tab import StatsTab
from benzintracker.ui.tabs.settings_tab import SettingsTab
from benzintracker.api.service import refresh_for_location
from benzintracker.api.tankerkonig import TankerkonigError
from benzintracker.database import models
from benzintracker.settings import app_settings
from benzintracker.translator import tr, translator


WINDOW_MIN_SIZE_WIDTH  = 1000
WINDOW_MIN_SIZE_HEIGHT = 850 
FIRST_CALL_DELAY = 500

TIMER_REFRESH_LABEL = 10_000        # One Minute;
JITTER_MAX_SEC = 180
MIN_MANUAL_REFRESH_SEC = 300        # 5 Minutes;


class MainWindow(QMainWindow):
    def __init__(self, initial_theme: str = "light"):
        super().__init__()
        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(WINDOW_MIN_SIZE_WIDTH, WINDOW_MIN_SIZE_HEIGHT)

        self._theme = initial_theme
        self._internal_ms = app_settings.refresh_interval_min * 60 * 1_000
        self._last_refresh: datetime | None = None

        self._build_ui()
        self._apply_theme(self._theme)
        self._setup_timer()
        translator.language_changed.connect(self.retranslate)

        # Make directly after start the first call (with a slight delay);
        QTimer.singleShot(FIRST_CALL_DELAY, self._do_refresh)



    # ---------------------------------------------------------------------------------------------------
    # Build UI;
    # ---------------------------------------------------------------------------------------------------
    def _build_ui(self):
        # Tabs;
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)         # Cleaner Look without extra borders;

        self.tab_map = MapTab(self)
        self.tab_table = TableTab(self)
        self.tab_stats = StatsTab(self)
        self.tab_settings = SettingsTab(self)

        self.tabs.addTab(self.tab_map, tr("tabs.map"))
        self.tabs.addTab(self.tab_table, tr("tabs.prices"))
        self.tabs.addTab(self.tab_stats, tr("tabs.stats"))
        self.tabs.addTab(self.tab_settings, tr("tabs.settings"))

        self.setCentralWidget(self.tabs)

        # Toolbar;
        toolbar = QToolBar("Actions", self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setStyleSheet(
            "QToolBar { border: none; padding: 4px 8px, spacing: 8px; }"
        )

        self.btn_manual_refresh = QPushButton(tr("toolbar.refresh_now"))
        self.btn_manual_refresh.setToolTip(tr("toolbar.refresh_now"))
        self.btn_manual_refresh.clicked.connect(self._on_manual_refresh)
        toolbar.addWidget(self.btn_manual_refresh)

        self.label_manual_hint = QLabel("")
        self.label_manual_hint.setObjectName("label_status")
        self.label_manual_hint.setContentsMargins(12, 0, 0, 0)
        toolbar.addWidget(self.label_manual_hint)

        self.addToolBar(toolbar)
        self.insertToolBarBreak(toolbar)

        # Statusbar;
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.label_version = QLabel(f"Version: {__version__}")
        self.label_version.setObjectName("label_status")

        self.label_last_refresh = QLabel(tr("status.no_refresh"))
        self.label_last_refresh.setObjectName("label_status")

        self.label_next_refresh = QLabel("")
        self.label_last_refresh.setObjectName("label_status")

        self.label_error = QLabel("")
        self.label_error.setObjectName("label_error")

        self.status_bar.addWidget(self.label_version)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.label_last_refresh)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.label_next_refresh)
        self.status_bar.addWidget(self.label_error)

        # Signal from the settings tab;
        self.tab_settings.settings_changed.connect(self._on_settings_changed)
        self.tab_table.station_selected.connect(self._on_station_selected)

    
    # Timer;
    def _next_interval_ms(self) -> int:
        """
        Calculate the next call interval with random jitter.
        Base interval (from settings) + random time between [0, 180] seconds.
        """
        jitter_ms = random.randint(0, JITTER_MAX_SEC * 1_000)
        return self._internal_ms + jitter_ms


    def _setup_timer(self):
        """
        Create the QTimer for the automatic refresh.
        """
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self._do_refresh)
        self.refresh_timer.start(self._next_interval_ms())

        # Second timer for the statusbar (refresh every minute);
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_next_refresh_label)
        self.countdown_timer.timeout.connect(self._update_manual_refresh_button)
        self.countdown_timer.start(TIMER_REFRESH_LABEL)

        # Deactivate the button at startup;
        self.btn_manual_refresh.setEnabled(False)
        self.label_manual_hint.setText(tr("toolbar.waiting_first"))


    def _restart_timer(self):
        """
        Restart the timer with a new interval.
        """
        self.refresh_timer.stop()
        self.refresh_timer.start(self._next_interval_ms())

    
    def _do_refresh(self):
        """
        Is called by QTimer (and at start).
        Reads the current location from the DB and calls the API.
        """
        loc = models.get_default_location()
        if loc is None:
            self.label_error.setText(tr("status.no_location"))
            return

        self.label_error.setText("")
        self.label_last_refresh.setText(tr("status.refreshing"))

        try:
            stations = refresh_for_location(
                lat=loc["lat"],
                lng=loc["lng"],
                radius_km=loc["radius_km"]
            )

        except TankerkonigError as e:
            self.label_error.setText(f"{e}")
            self.label_last_refresh.setText(tr("status.last_refresh_failed"))
            return

        self._last_refresh = datetime.now()
        self.label_last_refresh.setText(
            tr("status.last_refresh", time=self._last_refresh.strftime('%H:%M Uhr'))
        )
        self.refresh_timer.start(self._next_interval_ms())
        self._update_next_refresh_label()

        # Fill tabs with the new data;
        self.tab_table.update_data(stations)
        self.tab_map.update_data(stations)
        self.tab_stats.update_data(stations)

        self._update_manual_refresh_button()

    
    def _update_manual_refresh_button(self):
        """
        Activate or deactivate the manual refresh button.
        It depends if the last refresh was at least 5 minutes ago.
        """
        if self._last_refresh is None:
            # No API call yet - deactivate the button at startup;
            self.btn_manual_refresh.setEnabled(False)
            self.label_manual_hint.setText(tr("toolbar.waiting_first"))
            return

        elapsed_sec = (datetime.now() - self._last_refresh).total_seconds()
        remaining_sec = int(MIN_MANUAL_REFRESH_SEC - elapsed_sec)

        if remaining_sec <= 0:
            self.btn_manual_refresh.setEnabled(True)
            self.label_manual_hint.setText("")

        else:
            self.btn_manual_refresh.setEnabled(False)
            remaining_min = remaining_sec // 60
            remaining_s = remaining_sec % 60
            if remaining_min > 0:
                self.label_manual_hint.setText(tr("toolbar.refresh_available_in", available_in_min=remaining_min))

            else:
                self.label_manual_hint.setText(tr("toolbar.refresh_available_in_sec", available_in_sec=remaining_s))


    def _on_manual_refresh(self):
        if self._last_refresh is not None:
            elapsed_sec = (datetime.now() - self._last_refresh).total_seconds()

            if elapsed_sec < MIN_MANUAL_REFRESH_SEC: return
        
        self.refresh_timer.stop()
        self._do_refresh()


    def _update_next_refresh_label(self):
        """
        Shows when the next refresh occurs.
        """
        remaining_ms = self.refresh_timer.remainingTime()
        if remaining_ms <= 0:
            self.label_next_refresh.setText(tr("status.next_refresh_soon"))
            return

        remaining_min = remaining_ms // 60_000
        remaining_sec = (remaining_ms % 60_000) // 1_000
        if remaining_min > 0:
            self.label_next_refresh.setText(tr("status.next_refresh_min", mins=remaining_min))

        else:
            self.label_next_refresh.setText(tr("status.next_refresh_sec", sec=remaining_sec))


    
    # ---------------------------------------------------------------------------------------------------
    # Theme;
    # ---------------------------------------------------------------------------------------------------
    def _apply_theme(self, theme: str):
        self._theme = theme
        app_settings.theme = theme
        apply_theme(theme)
        self.tab_stats.set_theme(theme == "dark")
        self.tab_map.set_theme(theme == "dark")



    # ---------------------------------------------------------------------------------------------------
    # Slots;
    # ---------------------------------------------------------------------------------------------------
    def retranslate(self):
        """
        Update the UI texts after a language change.
        """
        self.setWindowTitle(tr("app.title"))
        self.tabs.setTabText(0, tr("tabs.map"))
        self.tabs.setTabText(1, tr("tabs.prices"))
        self.tabs.setTabText(2, tr("tabs.stats"))
        self.tabs.setTabText(3, tr("tabs.settings"))
        self.btn_manual_refresh.setText(tr("toolbar.refresh_now"))
        self._update_manual_refresh_button()
        self._update_next_refresh_label()


    def _on_settings_changed(self, theme: str, interval_min: int):
        """
        Reacts to changes in the settings tab.
        """
        if theme != self._theme: self._apply_theme(theme)

        new_interval_ms = interval_min * 60 * 1_000
        if new_interval_ms != self._internal_ms:
            self._internal_ms = new_interval_ms
            app_settings.refresh_interval_min = interval_min
            self._restart_timer()
            self._update_next_refresh_label()


    def _on_station_selected(self, station_id: str):
        """
        Jump to the Map-Tab and center onto the chosen station.
        """
        self.tabs.setCurrentWidget(self.tab_map)
        self.tab_map.focus_station(station_id)