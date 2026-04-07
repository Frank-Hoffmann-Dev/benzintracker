"""
config.py - Central Configuration for 'Benzintracker'.
API-Key and other settings are stored here.

The path to the database points according to each platform:
    - Linux:            ~/.local/share/benzintracker/
    - maxOS:            ~/Library/Application Support/benzintracker/
    - Windows:          C:\\Users\\<n>\\AppData\\Roaming\\benzintracker\\
"""
import os
from platformdirs import user_data_dir

# Package Name (it's used for the directory);
APP_NAME = "benzintracker"

# Tankerkönig API;
API_KEY = os.environ.get("TANKERKOENIG_API_KEY", "")
API_BASE_URL = "https://creativecommons.tankerkoenig.de/json"

def _get_data_dir() -> str:
    """
    Detect the data directory (cross-platform).
    Create it immediately if it does not exist yet.
    """
    data_dir = user_data_dir(APP_NAME)
    data_dir = os.path.join(
        os.path.expanduser("~"), ".local", "share", APP_NAME
    )
    os.makedirs(data_dir, exist_ok=True)

    return data_dir


def _resolve_db_path() -> str:
    """
    Reads the database path from QSettings if it's already stored, else set default in DATA_DIR.
    It is called lazy, to make sure that QApplication already exists.
    """
    return os.path.join(DATA_DIR, "benzintracker.db")
    

# Databank;
DATA_DIR = _get_data_dir()
DB_PATH = _resolve_db_path()

# Default Settings;
DEFAULT_RADIUS_KM = 5
DEFAULT_FUEL_TYPE = "e5"
REFRESH_INTERVAL_MIN = 30