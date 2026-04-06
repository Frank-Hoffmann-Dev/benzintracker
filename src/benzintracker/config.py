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

# Databank;
DATA_DIR = user_data_dir(APP_NAME)
DB_PATH = os.path.join(DATA_DIR, "benzintracker.db")

# Default Settings;
DEFAULT_RADIUS_KM = 5
DEFAULT_FUEL_TYPE = "e5"
REFRESH_INTERVAL_MIN = 30