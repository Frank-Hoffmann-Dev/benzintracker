"""
settings_tab.py

Settings Tab with:
    - Input for API-Key and validation
    - Setting of own location (Name, Lat, Lng, Radius)
    - Setting Refresh-Interval
    - Theme Toggle (Light / Dark)

Signals:
    settings_changed - triggers when user saves the settings. Main Window listens and applies changes.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox,
    QDoubleSpinBox, QGroupBox, QComboBox, QMessageBox
)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Signal

from benzintracker.api.tankerkonig import TankerkonigClient, TankerkonigError
from benzintracker.database import models
from benzintracker import config
from benzintracker.settings import app_settings


class SettingsTab(QWidget):
    settings_changed = Signal(str, int)     # (theme, interval_min)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme = app_settings.theme or "light"
        self._build_ui()
        self._load_settings()



    # ---------------------------------------------------------------------------------------------------
    # Build UI;
    # ---------------------------------------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(16)

        root.addWidget(self._build_api_group())
        root.addWidget(self._build_location_group())
        root.addWidget(self._build_refresh_group())
        root.addWidget(self._build_theme_group())
        root.addStretch()


    def _build_api_group(self) -> QGroupBox:
        box = QGroupBox("API-Key")

        root = QVBoxLayout(box)
        row = QHBoxLayout(box)

        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.Password)
        self.input_api_key.setPlaceholderText("Enter Tankerkönig API-KEY...")

        self.btn_validate = QPushButton("Check")
        self.btn_validate.setObjectName("btn_secondary")
        self.btn_validate.clicked.connect(self._validate_api_key)

        self.btn_save_key = QPushButton("Save")
        self.btn_save_key.clicked.connect(self._save_api_key)

        self.btn_delete_key = QPushButton("Remove")
        self.btn_delete_key.setObjectName("btn_secondary")
        self.btn_delete_key.clicked.connect(self._delete_api_key)

        row.addWidget(self.input_api_key, stretch=1)
        row.addWidget(self.btn_validate)
        row.addWidget(self.btn_save_key)
        row.addWidget(self.btn_delete_key)

        self.label_key_status = QLabel("")
        self.label_key_status.setObjectName("label_status")

        self.label_keyring_hint = QLabel(
            "No Keyring available - API-Key only saved for this one session."
            if not app_settings.keyring_available() else ""
        )
        self.label_keyring_hint.setObjectName("label_error")

        root.addLayout(row)
        root.addWidget(self.label_key_status)
        root.addWidget(self.label_keyring_hint)

        return box


    def _build_location_group(self) -> QGroupBox:
        box = QGroupBox("Location")
        form = QFormLayout(box)
        form.setSpacing(10)

        combo_row = QHBoxLayout()
        self.combo_locations = QComboBox()
        self.combo_locations.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._refresh_location_combo()

        self.btn_set_default = QPushButton("Set as Default")
        self.btn_set_default.setObjectName("btn_secondary")
        self.btn_set_default.clicked.connect(self._set_default_location)

        self.btn_delete_loc = QPushButton("Delete")
        self.btn_delete_loc.setObjectName("btn_secondary")
        self.btn_delete_loc.clicked.connect(self._delete_location)

        combo_row.addWidget(self.combo_locations, stretch=1)
        combo_row.addWidget(self.btn_set_default)
        combo_row.addWidget(self.btn_delete_loc)

        self.input_loc_name = QLineEdit()
        self.input_loc_name.setPlaceholderText("i.e. Home")

        self.input_lat = QLineEdit()
        self.input_lat.setPlaceholderText("i.e. 52.520008")
        self.input_lat.setValidator(QDoubleValidator(-90.0, 90.0, 6))

        self.input_lng = QLineEdit()
        self.input_lng.setPlaceholderText("i.e. 13.404954")
        self.input_lng.setValidator(QDoubleValidator(-180.0, 180.0, 6))

        self.input_radius = QDoubleSpinBox()
        self.input_radius.setRange(1.0, 25.0)
        self.input_radius.setSingleStep(0.5)
        self.input_radius.setSuffix(" km")
        self.input_radius.setValue(config.DEFAULT_RADIUS_KM)
        self.input_radius.setMinimumWidth(100)

        self.btn_save_loc = QPushButton("Save new Location")
        self.btn_save_loc.clicked.connect(self._save_location)

        form.addRow("Saved Location:", combo_row)
        form.addRow(QLabel(""))
        form.addRow("Name:", self.input_loc_name)
        form.addRow("Latitude:", self.input_lat)
        form.addRow("Longitude:", self.input_lng)
        form.addRow("Radius:", self.input_radius)
        form.addRow("", self.btn_save_loc)

        return box


    def _build_danger_group(self) -> QGroupBox:
        box = QGroupBox("Database")
        layout = QHBoxLayout(box)

        self.btn_reset_db = QPushButton("Reset Database")
        self.btn_reset_db.setStyleSheet(
            "QPushButton { background-color: #e53935; color: white; font-weight: bold; "
            "border: none; padding: 7px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #c62828; }"
            "QPushButton:pressed { background-color: #b71c1c; }"
        )
        self.btn_reset_db.clicked.connect(self._reset_database)

        label = QLabel("Delete all saved prices, stations and locations.")
        label.setObjectName("label_status")

        layout.addWidget(self.btn_reset_db)
        layout.addWidget(label)
        layout.addStretch()

        return box


    def _build_refresh_group(self) -> QGroupBox:
        box = QGroupBox("Refreshing Interval")
        layout = QHBoxLayout(box)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(5, 120)
        self.spin_interval.setSingleStep(5)
        self.spin_interval.setSuffix(" Minutes")
        self.spin_interval.setValue(
            app_settings.refresh_interval_min or
            config.REFRESH_INTERVAL_MIN
        )

        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self._apply_interval)

        layout.addWidget(QLabel("Interval:"))
        layout.addWidget(self.spin_interval)
        layout.addWidget(btn_apply)
        layout.addStretch()

        return box


    def _build_theme_group(self) -> QGroupBox:
        box = QGroupBox("Design")
        layout = QHBoxLayout(box)

        self.btn_ligth = QPushButton("⛅ Light")
        self.btn_ligth.setObjectName("btn_secondary")
        self.btn_ligth.clicked.connect(lambda: self._set_theme("light"))

        self.btn_dark = QPushButton("🌙 Dark")
        self.btn_dark.setObjectName("btn_secondary")
        self.btn_dark.clicked.connect(lambda: self._set_theme("dark"))

        layout.addWidget(self.btn_ligth)
        layout.addWidget(self.btn_dark)
        layout.addStretch()

        return box
    


    # ---------------------------------------------------------------------------------------------------
    # Actions;
    # ---------------------------------------------------------------------------------------------------
    def _validate_api_key(self):
        key = self.input_api_key.text().strip()
        if not key:
            self.label_key_status.setText("Enter first an API-Key.")
            return

        self.btn_validate.setEnabled(False)
        self.label_key_status.setText("Checking...")

        client = TankerkonigClient(api_key=key)
        if client.validate_api_key(): self.label_key_status.setText("✅ API-Key is valid.")
        else: self.label_key_status.setText("❌ API-Key is invalid or no connection.")

        self.btn_validate.setEnabled(True)


    def _save_api_key(self):
        """
        Save the API-KEY into the config and as environment variable.
        """
        key = self.input_api_key.text().strip()
        if not key: return

        app_settings.api_key = key
        if app_settings.keyring_available():
            self.label_key_status.setText("✅ API-Key safely stored in the systems pwd storage.")
        
        else:
            self.label_key_status.setText("✅ API-Key saved (only this session).")


    def _delete_api_key(self):
        app_settings.delete_api_key()
        self.input_api_key.clear()
        self.label_key_status.setText("API-Key removed.")


    def _save_location(self):
        name = self.input_loc_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Location", "Please add a name.")
            return

        try:
            lat = float(self.input_lat.text().replace(",", "."))
            lng = float(self.input_lng.text().replace(",", "."))

        except ValueError:
            QMessageBox.warning(self, "Location", "Enter valid coordinates.")
            return

        models.save_location(
            name=name,
            lat=lat,
            lng=lng,
            radius_km=self.input_radius.value()
        )
        self._refresh_location_combo()
        self.input_loc_name.clear()
        self.input_lat.clear()
        self.input_lng.clear()


    def _set_default_location(self):
        loc_id = self.combo_locations.currentData()
        if loc_id is None: return

        models.set_default_location(loc_id)
        self._refresh_location_combo()

        loc = models.get_default_location()
        if loc:
            self.input_lat.setText(str(loc["lat"]))
            self.input_lng.setText(str(loc["lng"]))
            self.input_radius.setValue(loc["radius_km"])

        QMessageBox.information(
            self, "Location",
            f"'{self.combo_locations.currentText()}' was set as the default location. "
            "With the next Refresh the data for the new location is retrieved."
        )


    def _delete_location(self):
        loc_id = self.combo_locations.currentData()
        if loc_id is None: return

        models.delete_location(loc_id)
        self._refresh_location_combo()


    def _apply_interval(self):
        interval = self.spin_interval.value()
        self.settings_changed.emit(self._current_theme, interval)
        app_settings.refresh_interval_min = interval


    def _set_theme(self, theme: str):
        self._current_theme = theme
        self.settings_changed.emit(theme, self.spin_interval.value())
        app_settings.theme = theme


    def _refresh_location_combo(self):
        self.combo_locations.clear()
        for loc in models.get_all_locations():
            label = f"{loc['name']} ({loc['lat']:.4f}, {loc['lng']:.4f})"
            self.combo_locations.addItem(label, userData=loc["id"])


    def _reset_database(self):
        """
        Delete all data once the user confirms.
        """
        reply = QMessageBox.warning(
            self,
            "Reset Database",
            "ALL data will be deleted. Are you sure?\n\n"
            "This cannot be reversed.",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        if reply != QMessageBox.Yes: return

        models.reset_database()

        self._refresh_location_combo()
        self.input_lat.clear()
        self.input_lng.clear()
        self.input_radius.setValue(5.0)

        QMessageBox.information(
            self, "Reset Database",
            "All data was successfully deleted."
        )


    def _load_settings(self):
        """
        Enter saved values at start.
        """
        if config.API_KEY: self.input_api_key.setText(config.API_KEY)

        loc = models.get_default_location()
        if loc:
            self.input_lat.setText(str(loc["lat"]))
            self.input_lng.setText(str(loc["lng"]))
            self.input_radius.setValue(loc["radius_km"])