"""
settings_tab.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: All Settings for managing the application.
=========================================================================================

Settings Tab with:
    - Input for API-Key and validation
    - Setting of own location (Name, Lat, Lng, Radius)
    - Setting Refresh-Interval
    - Theme Toggle (Light / Dark)

Signals:
    settings_changed - triggers when user saves the settings. Main Window listens and applies changes.
"""
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox,
    QDoubleSpinBox, QGroupBox, QComboBox, QMessageBox,
    QScrollArea, QFileDialog, QCheckBox, QSystemTrayIcon
)
from PySide6.QtGui import QDoubleValidator, QPalette, QColor
from PySide6.QtCore import Qt, Signal

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
        # ScrollArea;
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        # Inner Widget for all groups;
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)

        root.addWidget(self._build_api_group())
        root.addWidget(self._build_location_group())
        root.addWidget(self._build_refresh_group())
        root.addWidget(self._build_theme_group())
        root.addWidget(self._build_language_group())
        root.addWidget(self._build_tray_group())
        root.addWidget(self._build_database_group())
        root.addStretch()
        inner.setLayout(root)

        scroll.setWidget(inner)

        # Outer layout;
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.setLayout(outer)


    def _build_api_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_api"))
        root = QVBoxLayout(box)

        row = QHBoxLayout(box)
        self.input_api_key = QLineEdit(box)
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

        self.label_key_status = QLabel("", box)
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
        self.combo_locations = QComboBox(box)
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

        self.input_loc_name = QLineEdit(box)
        self.input_loc_name.setPlaceholderText(tr("settings.loc_name_placeholder"))

        self.input_lat = QLineEdit(box)
        self.input_lat.setPlaceholderText(tr("settings.loc_lat_placeholder"))
        self.input_lat.setValidator(QDoubleValidator(-90.0, 90.0, 6))

        self.input_lng = QLineEdit(box)
        self.input_lng.setPlaceholderText(tr("settings.loc_lng_placeholder"))
        self.input_lng.setValidator(QDoubleValidator(-180.0, 180.0, 6))

        self.input_radius = QDoubleSpinBox(box)
        self.input_radius.setRange(1.0, 25.0)
        self.input_radius.setSingleStep(0.5)
        self.input_radius.setSuffix(" km")
        self.input_radius.setValue(config.DEFAULT_RADIUS_KM)
        self.input_radius.setMinimumWidth(100)

        self.btn_save_loc = QPushButton(tr("settings.btn_save_loc"), box)
        self.btn_save_loc.clicked.connect(self._save_location)

        self._lbl_saved_locations = QLabel(tr("settings.label_saved_locations"))
        self._lbl_loc_name = QLabel(tr("settings.label_name"))
        self._lbl_loc_lat = QLabel(tr("settings.label_lat"))
        self._lbl_loc_lng = QLabel(tr("settings.label_lng"))
        self._lbl_loc_radius = QLabel(tr("settings.label_radius"))

        form.addRow(self._lbl_saved_locations, combo_row)
        form.addRow(QLabel(""))
        form.addRow(self._lbl_loc_name, self.input_loc_name)
        form.addRow(self._lbl_loc_lat, self.input_lat)
        form.addRow(self._lbl_loc_lng, self.input_lng)
        form.addRow(self._lbl_loc_radius, self.input_radius)
        form.addRow("", self.btn_save_loc)

        return box


    def _build_language_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_language"))
        layout = QHBoxLayout(box)

        self.label_language = QLabel(tr("settings.label_language"), box)
        self.combo_language = QComboBox(box)
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


    def _build_tray_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_tray"))
        layout = QVBoxLayout(box)

        self.check_tray = QCheckBox(tr("settings.tray_enable"), box)
        self.check_tray.setChecked(app_settings.tray_enabled)

        self.label_tray_hint = QLabel("", box)
        self.label_tray_hint.setObjectName("label_status")
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.label_tray_hint.setText(
                tr("settings.tray_not_available")
            )
            self.check_tray.setEnabled(False)

        self.check_tray.stateChanged.connect(self._on_tray_changed)

        layout.addWidget(self.check_tray)
        layout.addWidget(self.label_tray_hint)

        return box


    def _build_database_group(self) -> QGroupBox:
        """
        Group with the database path setting and reset-button.
        A custom path can be set or chosen via file dialog.
        After changing the database path, the application needs to be restarted.
        """
        box = QGroupBox(tr("settings.group_database"))
        root = QVBoxLayout(box)

        # DB Path;
        form = QFormLayout()
        form.setSpacing(8)

        path_row = QHBoxLayout()
        self.input_db_path = QLineEdit(box)
        self.input_db_path.setPlaceholderText(config.DB_PATH)
        self.input_db_path.setText(app_settings.db_path or config.DB_PATH)
        self.input_db_path.setMinimumWidth(300)

        self.btn_browse_db = QPushButton("...", box)
        self.btn_browse_db.setFixedWidth(36)
        self.btn_browse_db.setToolTip(tr("settings.db_browse_tooltip"))
        self.btn_browse_db.clicked.connect(self._browse_db_path)

        self.btn_save_db_path = QPushButton(tr("settings.btn_save_db_path"), box)
        self.btn_save_db_path.clicked.connect(self._save_db_path)

        path_row.addWidget(self.input_db_path, stretch=1)
        path_row.addWidget(self.btn_browse_db)
        path_row.addWidget(self.btn_save_db_path)

        self.label_db_path_status = QLabel("", box)
        self.label_db_path_status.setObjectName("label_status")

        self._lbl_db_path = QLabel(tr("settings.label_db_path"))
        form.addRow(self._lbl_db_path, path_row)
        form.addRow("", self.label_db_path_status)
        root.addLayout(form)

        separator = QWidget(box)
        separator.setFixedHeight(1)
        separator.setAutoFillBackground(True)
        sep_palette = separator.palette()
        sep_palette.setColor(QPalette.ColorRole.Window, QColor(128, 128, 128, 80))
        separator.setPalette(sep_palette)
        root.addWidget(separator)

        # Reset Button;
        reset_row = QHBoxLayout()
        self.btn_reset_db = QPushButton(tr("settings.btn_reset_db"), box)

        danger_palette = self.btn_reset_db.palette()
        danger_palette.setColor(QPalette.ColorRole.Button, QColor("#e53935"))
        danger_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))

        self.btn_reset_db.setPalette(danger_palette)
        self.btn_reset_db.setAutoFillBackground(True)
        self.btn_reset_db.clicked.connect(self._reset_database)

        self.label_reset_hint = QLabel(tr("settings.reset_db_label"), box)
        self.label_reset_hint.setObjectName("label_status")

        reset_row.addWidget(self.btn_reset_db)
        reset_row.addWidget(self.label_reset_hint)
        reset_row.addStretch()
        root.addLayout(reset_row)

        return box


    def _build_refresh_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_refresh"))
        layout = QHBoxLayout(box)

        self.spin_interval = QSpinBox(box)
        self.spin_interval.setRange(5, 120)
        self.spin_interval.setSingleStep(5)
        self.spin_interval.setSuffix(tr("settings.interval_suffix"))
        self.spin_interval.setValue(
            app_settings.refresh_interval_min or
            config.REFRESH_INTERVAL_MIN
        )

        btn_apply = QPushButton(tr("settings.btn_apply"), box)
        btn_apply.clicked.connect(self._apply_interval)

        self._lbl_interval = QLabel(tr("settings.label_interval"))
        layout.addWidget(self._lbl_interval)
        layout.addWidget(self.spin_interval)
        layout.addWidget(btn_apply)
        layout.addStretch()

        return box


    def _build_theme_group(self) -> QGroupBox:
        box = QGroupBox(tr("settings.group_theme"))
        layout = QHBoxLayout(box)

        self.btn_light = QPushButton(tr("settings.btn_light"), box)
        self.btn_light.setObjectName("btn_secondary")
        self.btn_light.clicked.connect(lambda: self._set_theme("light"))

        self.btn_dark = QPushButton(tr("settings.btn_dark"), box)
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


    def _set_theme(self, theme: str):
        self._current_theme = theme
        self.settings_changed.emit(theme, self.spin_interval.value())


    def _refresh_location_combo(self):
        self.combo_locations.clear()
        for loc in models.get_all_locations():
            star = " ★" if loc["is_default"] else ""
            label = f"{loc['name']}{star} ({loc['lat']:.4f}, {loc['lng']:.4f})"
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
        from PySide6.QtWidgets import QGroupBox as GB

        keys = [
            "settings.group_api", "settings.group_location",
            "settings.group_refresh", "settings.group_theme",
            "settings.group_language", "settings.group_tray",
            "settings.group_database"
        ]

        for box, key in zip(self.findChildren(GB), keys):
            box.setTitle(tr(key))

        # Buttons;
        self.btn_validate.setText(tr("settings.btn_validate"))
        self.btn_save_key.setText(tr("settings.btn_save_key"))
        self.btn_delete_key.setText(tr("settings.btn_delete_key"))
        self.btn_set_default.setText(tr("settings.btn_set_default"))
        self.btn_delete_loc.setText(tr("settings.btn_delete_loc"))
        self.btn_save_loc.setText(tr("settings.btn_save_loc"))
        self.btn_light.setText(tr("settings.btn_light"))
        self.btn_dark.setText(tr("settings.btn_dark"))
        self.btn_reset_db.setText(tr("settings.btn_reset_db"))
        self.btn_save_db_path.setText(tr("settings.btn_save_db_path"))

        # Placeholders;
        self.input_api_key.setPlaceholderText(tr("settings.api_placeholder"))
        self.input_loc_name.setPlaceholderText(tr("settings.loc_name_placeholder"))
        self.input_lat.setPlaceholderText(tr("settings.loc_lat_placeholder"))
        self.input_lng.setPlaceholderText(tr("settings.loc_lng_placeholder"))

        # Form row labels;
        self._lbl_saved_locations.setText(tr("settings.label_saved_locations"))
        self._lbl_loc_name.setText(tr("settings.label_name"))
        self._lbl_loc_lat.setText(tr("settings.label_lat"))
        self._lbl_loc_lng.setText(tr("settings.label_lng"))
        self._lbl_loc_radius.setText(tr("settings.label_radius"))
        self._lbl_interval.setText(tr("settings.label_interval"))
        self.label_language.setText(tr("settings.label_language"))
        self._lbl_db_path.setText(tr("settings.label_db_path"))
        self.check_tray.setText(tr("settings.tray_enabled"))


    def _on_tray_changed(self, state: int):
        enabled = bool(state)
        app_settings.tray_enabled = enabled

        main_window = self.window()
        if hasattr(main_window, "_update_tray_mode"):
            main_window._update_tray_mode(enabled)
 

    def _on_language_changed(self, index: int):
        locale = self.combo_language.itemData(index)
        if locale and locale != translator.current_locale:
            translator.set_language(locale)
            app_settings.language = locale


    def _browse_db_path(self):
        current = self.input_db_path.text() or config.DB_PATH
        start_dir = os.path.dirname(current)

        path, _ = QFileDialog.getSaveFileName(
            self, tr("settings.db_browse_title"),
            start_dir,
            tr("settings.db_browse_file_desc")
        )

        if path: self.input_db_path.setText(os.path.normpath(path))

    
    def _save_db_path(self):
        """
        Save the new db path in QSettings.
        The path will be used after restart.
        """
        raw = self.input_db_path.text().strip()
        if not raw: return

        path = os.path.normpath(raw)

        # Check if the directory exists or create it;
        db_dir = os.path.dirname(path)
        if db_dir and not os.path.exists(db_dir):
            reply = QMessageBox.question(
                self, tr("settings.db_path_title"),
                tr("settings.db_dir_create", path=db_dir),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )

            if reply != QMessageBox.StandardButton.Yes: return

            try: os.makedirs(db_dir, exist_ok=True)
            except OSError as e:
                QMessageBox.critical(
                    self, tr("settings.db_path_title"),
                    tr("settings.db_dir_error", error=str(e))
                )
                return

        app_settings.db_path = path
        self.label_db_path_status.setText(tr("settings.db_path_saved"))


    def _load_settings(self):
        """
        Enter saved values at start.
        """
        key = app_settings.api_key
        if key: self.input_api_key.setText(key)

        self.spin_interval.setValue(app_settings.refresh_interval_min)

        saved_path = app_settings.db_path
        if saved_path: self.input_db_path.setText(saved_path)

        self.check_tray.setChecked(app_settings.tray_enabled)