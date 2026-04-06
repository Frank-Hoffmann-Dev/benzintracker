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
from benzintracker.translator import tr, translator


class SettingsTab(QWidget):
    settings_changed = Signal(str, int)     # (theme, interval_min)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme = app_settings.theme or "light"
        self._build_ui()
        self._load_settings()
        translator.language_changed.connect(self.retranslate)



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
        root.addWidget(self._build_language_group())
        root.addWidget(self._build_danger_group())
        root.addStretch()


    def _build_api_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_api"))

        root = QVBoxLayout(box)
        row = QHBoxLayout(box)

        self.input_api_key = QLineEdit()
        self.input_api_key.setEchoMode(QLineEdit.Password)
        self.input_api_key.setPlaceholderText(tr("settings.api_placeholder"))

        self.btn_validate = QPushButton(tr("settings.btn_validate"))
        self.btn_validate.setObjectName("btn_secondary")
        self.btn_validate.clicked.connect(self._validate_api_key)

        self.btn_save_key = QPushButton(tr("settings.btn_save_key"))
        self.btn_save_key.clicked.connect(self._save_api_key)

        self.btn_delete_key = QPushButton(tr("settings.btn_delete_key"))
        self.btn_delete_key.setObjectName("btn_secondary")
        self.btn_delete_key.clicked.connect(self._delete_api_key)

        row.addWidget(self.input_api_key, stretch=1)
        row.addWidget(self.btn_validate)
        row.addWidget(self.btn_save_key)
        row.addWidget(self.btn_delete_key)

        self.label_key_status = QLabel("")
        self.label_key_status.setObjectName("label_status")

        self.label_keyring_hint = QLabel(
            tr("settings.no_keyring")
            if not app_settings.keyring_available() else ""
        )
        self.label_keyring_hint.setObjectName("label_error")

        root.addLayout(row)
        root.addWidget(self.label_key_status)
        root.addWidget(self.label_keyring_hint)

        return box


    def _build_location_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_location"))
        form = QFormLayout(box)
        form.setSpacing(10)

        combo_row = QHBoxLayout()
        self.combo_locations = QComboBox()
        self.combo_locations.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._refresh_location_combo()

        self.btn_set_default = QPushButton(tr("settings.btn_set_default"))
        self.btn_set_default.setObjectName("btn_secondary")
        self.btn_set_default.clicked.connect(self._set_default_location)

        self.btn_delete_loc = QPushButton(tr("settings.btn_delete_loc"))
        self.btn_delete_loc.setObjectName("btn_secondary")
        self.btn_delete_loc.clicked.connect(self._delete_location)

        combo_row.addWidget(self.combo_locations, stretch=1)
        combo_row.addWidget(self.btn_set_default)
        combo_row.addWidget(self.btn_delete_loc)

        self.input_loc_name = QLineEdit()
        self.input_loc_name.setPlaceholderText(tr("settings.loc_name_placeholder"))

        self.input_lat = QLineEdit()
        self.input_lat.setPlaceholderText(tr("settings.loc_lat_placeholder"))
        self.input_lat.setValidator(QDoubleValidator(-90.0, 90.0, 6))

        self.input_lng = QLineEdit()
        self.input_lng.setPlaceholderText(tr("settings.loc_lng_placeholder"))
        self.input_lng.setValidator(QDoubleValidator(-180.0, 180.0, 6))

        self.input_radius = QDoubleSpinBox()
        self.input_radius.setRange(1.0, 25.0)
        self.input_radius.setSingleStep(0.5)
        self.input_radius.setSuffix(" km")
        self.input_radius.setValue(config.DEFAULT_RADIUS_KM)
        self.input_radius.setMinimumWidth(100)

        self.btn_save_loc = QPushButton(tr("settings.btn_save_loc"))
        self.btn_save_loc.clicked.connect(self._save_location)

        form.addRow(tr("settings.label_saved_locations"), combo_row)
        form.addRow(QLabel(""))
        form.addRow(tr("settings.label_name"), self.input_loc_name)
        form.addRow(tr("settings.label_lat"), self.input_lat)
        form.addRow(tr("settings.label_lng"), self.input_lng)
        form.addRow(tr("settings.label_radius"), self.input_radius)
        form.addRow("", self.btn_save_loc)

        return box


    def _build_language_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_language"))
        layout = QHBoxLayout(box)

        self.label_language = QLabel(tr("settings.label_language"))
        self.combo_language = QComboBox()
        for locale, name in translator.available_languages():
            self.combo_language.addItem(name, userData=locale)

        # Set current locale;
        current = translator.current_locale
        idx = self.combo_language.findData(current)
        if idx >= 0: self.combo_language.setCurrentIndex(idx)

        self.combo_language.currentIndexChanged.connect(self._on_language_changed)

        layout.addWidget(self.label_language)
        layout.addWidget(self.combo_language)
        layout.addStretch()

        return box


    def _build_danger_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_database"))
        layout = QHBoxLayout(box)

        self.btn_reset_db = QPushButton(tr("settings.btn_reset_db"))

        # Danger colors above the palette instead of hard CSS;
        from PySide6.QtGui import QPalette, QColor

        danger_palette = self.btn_reset_db.palette()
        danger_palette.setColor(QPalette.ColorRole.Button,     QColor("#e53935"))
        danger_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
        self.btn_reset_db.setPalette(danger_palette)
        self.btn_reset_db.setAutoFillBackground(True)
        self.btn_reset_db.clicked.connect(self._reset_database)

        label = QLabel(tr("settings.reset_db_label"))
        label.setObjectName("label_status")

        layout.addWidget(self.btn_reset_db)
        layout.addWidget(label)
        layout.addStretch()

        return box


    def _build_refresh_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_refresh"))
        layout = QHBoxLayout(box)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(5, 120)
        self.spin_interval.setSingleStep(5)
        self.spin_interval.setSuffix(tr("settings.interval_suffix"))
        self.spin_interval.setValue(
            app_settings.refresh_interval_min or
            config.REFRESH_INTERVAL_MIN
        )

        btn_apply = QPushButton(tr("settings.btn_apply"))
        btn_apply.clicked.connect(self._apply_interval)

        layout.addWidget(QLabel(tr("settings.label_interval")))
        layout.addWidget(self.spin_interval)
        layout.addWidget(btn_apply)
        layout.addStretch()

        return box


    def _build_theme_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_theme"))
        layout = QHBoxLayout(box)

        self.btn_light = QPushButton(tr("settings.btn_light"))
        self.btn_light.setObjectName("btn_secondary")
        self.btn_light.clicked.connect(lambda: self._set_theme("light"))

        self.btn_dark = QPushButton(tr("settings.btn_dark"))
        self.btn_dark.setObjectName("btn_secondary")
        self.btn_dark.clicked.connect(lambda: self._set_theme("dark"))

        layout.addWidget(self.btn_light)
        layout.addWidget(self.btn_dark)
        layout.addStretch()

        return box
    


    # ---------------------------------------------------------------------------------------------------
    # Actions;
    # ---------------------------------------------------------------------------------------------------
    def _validate_api_key(self):
        key = self.input_api_key.text().strip()
        if not key:
            self.label_key_status.setText(tr("settings.key_empty"))
            return

        self.btn_validate.setEnabled(False)
        self.label_key_status.setText(tr("settings.key_checking"))

        client = TankerkonigClient(api_key=key)
        if client.validate_api_key(): self.label_key_status.setText(tr("settings.key_valid"))
        else: self.label_key_status.setText(tr("settings.key_invalid"))

        self.btn_validate.setEnabled(True)


    def _save_api_key(self):
        """
        Save the API-KEY into the config and as environment variable.
        """
        key = self.input_api_key.text().strip()
        if not key: return

        app_settings.api_key = key
        if app_settings.keyring_available():
            self.label_key_status.setText(tr("settings.key_saved_keyring"))
        
        else:
            self.label_key_status.setText(tr("settings.key_saved_session"))


    def _delete_api_key(self):
        app_settings.delete_api_key()
        self.input_api_key.clear()
        self.label_key_status.setText(tr("settings.key_deleted"))


    def _save_location(self):
        name = self.input_loc_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("settings.loc_title"), tr("settings.loc_name_required"))
            return

        try:
            lat = float(self.input_lat.text().replace(",", "."))
            lng = float(self.input_lng.text().replace(",", "."))

        except ValueError:
            QMessageBox.warning(self, tr("settings.group_location"), tr("settings.loc_coords_invalid"))
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
            self, tr("settings.loc_title"),
            tr("settings.loc_set_default_msg", name=self.combo_locations.currentText())
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
            tr("settings.reset_db_title"),
            tr("settings.reset_db_confirm"),
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
            self, tr("settings.reset_db_title"),
            tr("settings.reset_db_success")
        )

    def retranslate(self):
        """
        Updates all texts after locale change.
        """
        # GroupBox-Titel
        for box, key in zip(
            self.findChildren(__import__("PySide6.QtWidgets", fromlist=["QGroupBox"]).QGroupBox),
            ["settings.group_api", "settings.group_location", "settings.group_refresh",
             "settings.group_theme", "settings.group_language", "settings.group_database"]
        ):
            box.setTitle(tr(key))

        self.btn_validate.setText(tr("settings.btn_validate"))
        self.btn_save_key.setText(tr("settings.btn_save_key"))
        self.btn_delete_key.setText(tr("settings.btn_delete_key"))
        self.btn_set_default.setText(tr("settings.btn_set_default"))
        self.btn_delete_loc.setText(tr("settings.btn_delete_loc"))
        self.btn_save_loc.setText(tr("settings.btn_save_loc"))
        self.btn_light.setText(tr("settings.btn_light"))
        self.btn_dark.setText(tr("settings.btn_dark"))
        self.btn_reset_db.setText(tr("settings.btn_reset_db"))
        self.input_api_key.setPlaceholderText(tr("settings.api_placeholder"))
        self.input_loc_name.setPlaceholderText(tr("settings.loc_name_placeholder"))
        self.input_lat.setPlaceholderText(tr("settings.loc_lat_placeholder"))
        self.input_lng.setPlaceholderText(tr("settings.loc_lng_placeholder"))
 

    def _on_language_changed(self, index: int):
        locale = self.combo_language.itemData(index)
        if locale and locale != translator.current_locale:
            translator.set_language(locale)
            app_settings.language = locale


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