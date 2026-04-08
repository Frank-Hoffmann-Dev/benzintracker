# Benzintracker

A desktop application for fetching, storing and analysing fuel prices in your area – powered by the [Tankerkönig API](https://creativecommons.tankerkoenig.de/).

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Features

- **Map view** – Nearby stations on an interactive map, filterable by fuel type
- **Price table** – Sortable table of all stations with E5, E10 and Diesel prices; cheapest price per column is highlighted
- **Statistics** – Four charts: price history, daily average, station comparison and time-of-day analysis; all exportable as PNG, PDF or SVG
- **CSV export** – Export the price table as CSV (UTF-8 with BOM for Excel compatibility)
- **Automatic refresh** – Configurable interval with random jitter as required by the Tankerkönig terms of use
- **Manual refresh** – On demand via button, with a 2-minute cooldown between requests
- **Multiple locations** – Save any number of locations, set one as default
- **System tray** – Optionally keep running in the background; data continues to be fetched even when the window is closed
- **Light and dark theme** – Native styling via Qt Fusion + QPalette
- **Multilingual** – German and English included; additional languages can be added via a JSON file
- **Custom database path** – The SQLite file can be placed on a network drive or any other location
- **Secure API key storage** – Via the system-wide password manager (GNOME Keyring, KWallet, Windows Credential Manager, macOS Keychain)

---

## Requirements

- Python 3.11 or newer
- A free API key from [creativecommons.tankerkoenig.de](https://creativecommons.tankerkoenig.de/)

---

## Installation

### From PyPI

```bash
pip install benzintracker
```

### From source

```bash
git clone https://github.com/your-name/benzintracker.git
cd benzintracker
pip install -e .
```

### With optional developer dependencies

```bash
pip install -e ".[dev]"
```

---

## Usage

```bash
benzintracker
```

---

## First launch

1. **Enter your API key** – Go to *Settings → API Key*, enter your Tankerkönig key and click "Save". The key is stored securely in the system-wide password manager.

2. **Set your location** – Go to *Settings → Location*, enter your coordinates (latitude/longitude) and search radius, save the entry and set it as the default. You can look up your coordinates on [maps.google.com](https://maps.google.com) or [openstreetmap.org](https://www.openstreetmap.org).

3. **Start the first fetch** – The application automatically fetches data for the default location on startup.

### API key via environment variable (optional)

```bash
# Linux / macOS
export TANKERKOENIG_API_KEY="your-api-key"

# Windows (PowerShell)
$env:TANKERKOENIG_API_KEY = "your-api-key"
```

---

## Database

The SQLite database is stored in the platform-specific user data directory by default:

| Platform | Default path |
|----------|-------------|
| Linux    | `~/.local/share/benzintracker/benzintracker.db` |
| macOS    | `~/Library/Application Support/benzintracker/benzintracker.db` |
| Windows  | `C:\Users\<n>\AppData\Roaming\benzintracker\benzintracker.db` |

A custom path – for example on a network drive – can be set under *Settings → Database*. The change takes effect on the next application start.

> **Note:** SQLite on network drives (NFS, SMB) works reliably but may be slower with poor connectivity. The application automatically retries write operations when a temporary lock is encountered.

---

## Languages

Language files are located under `benzintracker/locales/` as JSON files. To add a new language:

1. Copy `benzintracker/locales/en.json` and rename it, e.g. `fr.json`
2. Update the `_meta` block:
   ```json
   "_meta": {
       "language": "Français",
       "locale": "fr",
       "author": "Your Name"
   }
   ```
3. Translate all values
4. Restart the application – the new language will appear automatically in the dropdown under *Settings → Language*

---

## System tray

The tray mode can be enabled under *Settings → System tray*. When active, closing the window does not quit the application – it keeps running in the background and continues fetching data.

- **Left-click** on the tray icon: show/hide the window
- **Right-click** on the tray icon: context menu with "Show window" and "Quit"

> ~~**Linux note:** On GNOME version 40 and later, the extension [AppIndicator and KStatusNotifierItem Support](https://extensions.gnome.org/extension/615/appindicator-support/) must be installed for the tray icon to be visible. On KDE, XFCE and Windows it works without any additional setup.~~

---

## Project structure

```
benzintracker/
├── api/
│   ├── tankerkonig.py      # API client
│   └── service.py          # Connects API and database
├── database/
│   ├── db.py               # Connection, initialisation, retry logic
│   └── models.py           # CRUD operations
├── ui/
│   ├── main_window.py      # Main window, timer, tray
│   ├── styles.py           # QPalette light/dark
│   └── tabs/
│       ├── map_tab.py      # Map view (Folium + QWebEngineView)
│       ├── table_tab.py    # Price table
│       ├── stats_tab.py    # Statistics (Matplotlib)
│       └── settings_tab.py # Settings
├── locales/
│   ├── de.json             # German
│   └── en.json             # English
├── config.py               # Central configuration
├── settings.py             # Persistent settings (QSettings + keyring)
├── translator.py           # Runtime translation
└── main.py                 # Entry point
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `PySide6` | GUI framework |
| `folium` | Map rendering (HTML/Leaflet) |
| `matplotlib` | Statistics charts |
| `numpy` | Trend line calculation |
| `requests` | HTTP requests to the Tankerkönig API |
| `platformdirs` | Platform-appropriate data paths |
| `keyring` | Secure API key storage |

---

## License

MIT License
```
Copyright 2026 Frank Hoffmann

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```


## AI Usage

I used the AI assistant **Anthropic Claude AI - Sonnet 4.6** to create this tool.

As a computer scientist, I have reviewed and approved every single line of code, and I understand the tool’s internal processes and how it works.
I didn’t just copy and paste the code from the AI.
Instead, I wrote it by hand, line by line, making changes whenever I deemed it necessary.

Nevertheless, there may still be errors or poor design choices.
Everyone is free to examine, modify, improve, fork the code or call it AI slop :D