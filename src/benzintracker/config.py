"""
config.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: Central Configuration for 'Benzintracker'.
=========================================================================================

The path to the database points according to each platform:
    - Linux:            ~/.local/share/benzintracker/
    - maxOS:            ~/Library/Application Support/benzintracker/
    - Windows:          C:\\Users\\<n>\\AppData\\Roaming\\benzintracker\\
"""
import os

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
    try:
        from platformdirs import user_data_dir
        data_dir = user_data_dir(APP_NAME)
    
    except ImportError:
        data_dir = os.path.join(os.path.expanduser("~"), ".local", "share", APP_NAME)

    os.makedirs(data_dir, exist_ok=True)
    return data_dir


# Databank;
DATA_DIR = _get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "benzintracker.db")

# Default Settings;
DEFAULT_RADIUS_KM = 5
DEFAULT_FUEL_TYPE = "e5"
REFRESH_INTERVAL_MIN = 30