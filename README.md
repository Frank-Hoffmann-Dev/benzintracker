# Benzintracker

Ein Desktop-Programm zum Abrufen, Speichern und Auswerten von Benzinpreisen in der Umgebung – powered by der [Tankerkönig API](https://creativecommons.tankerkoenig.de/).

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green)
![License](https://img.shields.io/badge/Lizenz-MIT-lightgrey)

---

## Features

- **Kartenansicht** – Tankstellen in der Umgebung auf einer interaktiven Karte, gefiltert nach Kraftstofftyp
- **Preistabelle** – Sortierbare Tabelle aller Stationen mit E5-, E10- und Diesel-Preisen; günstigster Preis je Spalte wird hervorgehoben
- **Statistiken** – Vier Grafiken: Preisverlauf, Tagesdurchschnitt, Stationsvergleich und Tageszeit-Analyse; alle exportierbar als PNG, PDF oder SVG
- **CSV-Export** – Preistabelle als CSV exportieren (UTF-8 mit BOM für Excel-Kompatibilität)
- **Automatische Aktualisierung** – Konfigurierbares Intervall mit zufälligem Jitter gemäß Tankerkönig-Nutzungsbedingungen
- **Manueller Refresh** – Auf Knopfdruck, mit 2-Minuten-Sperrzeit zwischen Abrufen
- **Mehrere Standorte** – Beliebig viele Standorte speichern, einen als Standard setzen
- **System Tray** – Optional im Hintergrund weiterlaufen lassen; Daten werden weiter abgerufen auch wenn das Fenster geschlossen ist
- **Hell- und Dunkel-Theme** – Natives Styling über Qt Fusion + QPalette
- **Mehrsprachig** – Deutsch und Englisch enthalten; weitere Sprachen per JSON-Datei ergänzbar
- **Benutzerdefinierter Datenbankpfad** – SQLite-Datei kann auf ein Netzlaufwerk oder einen anderen Ort gelegt werden
- **Sicherer API-Key-Speicher** – Über den systemweiten Passwort-Speicher (GNOME Keyring, KWallet, Windows Credential Manager, macOS Keychain)

---

## Voraussetzungen

- Python 3.11 oder neuer
- Ein kostenloser API-Key von [creativecommons.tankerkoenig.de](https://creativecommons.tankerkoenig.de/)

---

## Installation

### Aus PyPI

```bash
pip install benzintracker
```

### Aus dem Quellcode

```bash
git clone https://github.com/dein-name/benzintracker.git
cd benzintracker
pip install -e .
```

### Mit optionalen Entwickler-Abhängigkeiten

```bash
pip install -e ".[dev]"
```

---

## Starten

```bash
benzintracker
```

---

## Erster Start

1. **API-Key eintragen** – Unter *Einstellungen → API-Schlüssel* den Tankerkönig-Key eingeben und auf „Speichern" klicken. Der Key wird sicher im systemweiten Passwort-Speicher abgelegt.

2. **Standort festlegen** – Unter *Einstellungen → Standort* Koordinaten (Breitengrad/Längengrad) und Suchradius eintragen, speichern und als Standard setzen. Die Koordinaten des eigenen Standorts lassen sich z. B. über [maps.google.com](https://maps.google.com) oder [openstreetmap.org](https://www.openstreetmap.org) ermitteln.

3. **Ersten Abruf starten** – Die Anwendung ruft beim Start automatisch Daten für den Standard-Standort ab.

### API-Key als Umgebungsvariable (optional)

```bash
# Linux / macOS
export TANKERKOENIG_API_KEY="dein-api-key"

# Windows (PowerShell)
$env:TANKERKOENIG_API_KEY = "dein-api-key"
```

---

## Datenbank

Die SQLite-Datenbank wird standardmäßig im plattformspezifischen Nutzerdatenverzeichnis abgelegt:

| Plattform | Standardpfad |
|-----------|-------------|
| Linux     | `~/.local/share/benzintracker/benzintracker.db` |
| macOS     | `~/Library/Application Support/benzintracker/benzintracker.db` |
| Windows   | `C:\Users\<Name>\AppData\Roaming\benzintracker\benzintracker.db` |

Ein abweichender Pfad – z. B. auf einem Netzlaufwerk – kann unter *Einstellungen → Datenbank* festgelegt werden. Die Änderung wird beim nächsten Programmstart aktiv.

> **Hinweis:** SQLite auf Netzwerklaufwerken (NFS, SMB) funktioniert zuverlässig, kann aber bei schlechter Verbindung langsamer sein. Die Anwendung wiederholt Schreibvorgänge bei temporären Sperren automatisch.

---

## Sprachen

Sprachdateien liegen unter `benzintracker/locales/` als JSON-Dateien. Eine neue Sprache anlegen:

1. `benzintracker/locales/de.json` kopieren und umbenennen, z. B. `fr.json`
2. Den `_meta`-Block anpassen:
   ```json
   "_meta": {
       "language": "Français",
       "locale": "fr",
       "author": "Dein Name"
   }
   ```
3. Alle Werte übersetzen
4. Anwendung neu starten – die neue Sprache erscheint automatisch im Dropdown unter *Einstellungen → Sprache*

---

## System Tray

Unter *Einstellungen → Infobereich* kann der Tray-Modus aktiviert werden. Ist er aktiv, wird die Anwendung beim Schließen des Fensters nicht beendet, sondern läuft im Hintergrund weiter und ruft weiterhin Daten ab.

- **Linksklick** auf das Tray-Icon: Fenster ein-/ausblenden
- **Rechtsklick** auf das Tray-Icon: Kontextmenü mit „Fenster anzeigen" und „Beenden"

> **Linux-Hinweis:** Auf GNOME ab Version 40 muss die Extension [AppIndicator and KStatusNotifierItem Support](https://extensions.gnome.org/extension/615/appindicator-support/) installiert sein, damit das Tray-Icon sichtbar ist. Auf KDE, XFCE und Windows funktioniert es ohne weitere Einrichtung.

---

## Projektstruktur

```
benzintracker/
├── api/
│   ├── tankerkonig.py      # API-Client
│   └── service.py          # Verbindet API und Datenbank
├── database/
│   ├── db.py               # Verbindung, Initialisierung, Retry-Logik
│   └── models.py           # CRUD-Operationen
├── ui/
│   ├── main_window.py      # Hauptfenster, Timer, Tray
│   ├── styles.py           # QPalette Hell/Dunkel
│   └── tabs/
│       ├── map_tab.py      # Kartenansicht (Folium + QWebEngineView)
│       ├── table_tab.py    # Preistabelle
│       ├── stats_tab.py    # Statistiken (Matplotlib)
│       └── settings_tab.py # Einstellungen
├── locales/
│   ├── de.json             # Deutsch
│   └── en.json             # Englisch
├── config.py               # Zentrale Konfiguration
├── settings.py             # Persistente Einstellungen (QSettings + keyring)
├── translator.py           # Laufzeit-Übersetzung
└── main.py                 # Einstiegspunkt
```

---

## Abhängigkeiten

| Paket | Zweck |
|-------|-------|
| `PySide6` | GUI-Framework |
| `folium` | Kartenrendering (HTML/Leaflet) |
| `matplotlib` | Statistik-Grafiken |
| `numpy` | Trendlinien-Berechnung |
| `requests` | HTTP-Anfragen an die Tankerkönig API |
| `platformdirs` | Plattformgerechte Datenpfade |
| `keyring` | Sicherer API-Key-Speicher |

---

## Lizenz

MIT – siehe [LICENSE](LICENSE)