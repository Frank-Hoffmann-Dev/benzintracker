"""
settings.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: Persistent storage of application data via QSettings and keyring.
=========================================================================================

QSettings: For uncritical settings like theme and interval
    - Linux:   ~/.config/benzintracker/benzintracker.ini
    - macOS:   ~/Library/Preferences/benzintracker.plist
    - Windows: HKCU\\Software\\benzintracker\\benzintracker

keyring: API-Key in the systemwide password storage
    - Linux:   GNOME Keyring / KWallet
    - macOS:   Keychain
    - Windows: Credential Manager
"""
from benzintracker import config


# Constants for keyring;
_KEYRING_SERVICE = "benzintracker"
_KEYRING_USER = "tankerkonig_api_key"


def _keyring_available() -> bool:
    try:
        import keyring
        return True

    except ImportError:
        return False


class AppSettings:
    """
    Thin Wrapper for QSettings and keyring.
    Exported as Singelton 'app_settings'.
    """
    def __init__(self):
        # QSettings with organization + application for clean paths;
        self._qs = None         # Lazy load;

    @property
    def _q(self):
        """
        Return the QSettings instance.
        Create it during the first call - at this point QApplication must already exist.
        """
        if self._qs is None:
            from PySide6.QtCore import QSettings
            self._qs = QSettings("benzintracker", "benzintracker")

        return self._qs


    # Theme;
    @property
    def theme(self) -> str:
        return self._q.value("ui/theme", "light")

    @theme.setter
    def theme(self, value: str):
        self._q.setValue("ui/theme", value)
        self._q.sync()


    # Refresh Interval;
    @property
    def refresh_interval_min(self) -> int:
        return int(self._q.value("refresh/interval_min", config.REFRESH_INTERVAL_MIN))

    @refresh_interval_min.setter
    def refresh_interval_min(self, value: int):
        self._q.setValue("refresh/interval_min", value)
        self._q.sync()


    # Database Path;
    @property
    def db_path(self) -> str:
        return self._q.value("database/path", "")

    @db_path.setter
    def db_path(self, value: str):
        self._q.setValue("database/path", value)
        self._q.sync()


    # System Tray;
    @property
    def tray_enabled(self) -> bool:
        return self._q.value("ui/tray_enabled", False, type=bool)

    @tray_enabled.setter
    def tray_enabled(self, value: bool):
        self._q.setValue("ui/tray_enabled", value)
        self._q.sync()


    # Language;
    @property
    def language(self) -> str:
        return self._q.value("ui/language", "")

    @language.setter
    def language(self, value: str):
        self._q.setValue("ui/language", value)
        self._q.sync()

        
    # API-Key (keyring);
    @property
    def api_key(self) -> str:
        """
        Read the API-Key from the systemwide password storage.
        Fallback onto the environment variable if no keyring available.
        """
        if _keyring_available():
            import keyring
                
            key = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USER)
            return key or ""

        return config.API_KEY       # Fallback;

    @api_key.setter
    def api_key(self, value: str):
        """
        Save the API-Key in the systemwide password storage.
        """
        if _keyring_available():
            import keyring

            if value: keyring.set_password(_KEYRING_SERVICE, _KEYRING_USER, value)
            else: self.delete_api_key()

        # Also always set in config + environment variable (runtime);
        config.API_KEY = value
        import os
        os.environ["TANKERKONIG_API_KEY"] = value


    def delete_api_key(self):
        if _keyring_available():
            import keyring

            try: keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USER)
            except keyring.errors.PasswordDeleteError: pass

        config.API_KEY = ""
        import os
        os.environ.pop("TANKERKONIG_API_KEY", None)


    def keyring_available(self) -> bool:
        return _keyring_available()


# Singelton: Imported by every module;
app_settings = AppSettings()