"""
translator.py
Author: Frank Hoffmann
AI Assistent: Anthropic Claude AI - Sonnet 4.6
Date: 08.04.2026
License: MIT
Description: Central Translator for the runtime l10n.
=========================================================================================

Usage:
    from benzintracker.translator import tr, translator
    tr("app.title")                             # Simple string;
    tr("status.last_refresh", time="14:30")     # with placeholder;

Change Language:
    # Triggers signal;
    translator.set_language("en")

Language Files:
    benzintracker/locales/*.json
    Each file must have a '_meta' block with 'language' and 'locale'.
"""
import json
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QLocale


LOCALES_DIR = Path(__file__).parent / "locales"


class Translator(QObject):
    """
    Singelton class for all language files from the 'locales/' directory.
    """
    language_changed = Signal()

    def __init__(self):
        super().__init__()
        self._strings: dict[str, str] = {}
        self._available: dict[str, dict] = {}
        self._current_locale = "de"
        self._load_available()


    # Available Languages;
    def _load_available(self):
        """
        Read all *.json files from 'locales/' directory.
        """
        self._available = {}
        if not LOCALES_DIR.exists(): return

        for path in sorted(LOCALES_DIR.glob("*.json")):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)

                meta = data.get("_meta", {})
                locale = data.get("locale", path.stem)
                self._available[locale] = {
                    "language": meta.get("language", locale),
                    "path": path
                }

            except (json.JSONDecodeError, OSError): pass


    def available_languages(self) -> list[tuple[str, str]]:
        """
        Return a list of all available languages.
        """
        return [
            (locale, info["language"])
            for locale, info in self._available.items()
        ]

    
    # Set Language;
    def set_language(self, locale: str):
        """
        Load the l10n file and trigger the 'language_changed'.
        """
        if locale not in self._available:
            # Fallback: first available language;
            if self._available: locale = next(iter(self._available))
            else: return

        path = self._available[locale]["path"]
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # Filter '_meta' out;
            self._strings = {k: v for k, v in data.items() if k != "_meta"}
            self._current_locale = locale
            self.language_changed.emit()

        except (json.JSONDecodeError, OSError) as e:
            print(f"[ERROR] Failed to read l10n file '{path}': {e}")


    def detect_system_language(self) -> str:
        """
        Try to detect the system language.
        Fallback on "de" if nothing can be detected.
        """
        system_locale = QLocale.system().name()[:2].lower()

        if system_locale in self._available:
            return system_locale

        return "de" if "de" in self._available else next(iter(self._available), "de")


    @property
    def current_locale(self) -> str:
        return self._current_locale
    

    # Translation;
    def translate(self, key: str, **kwargs) -> str:
        """
        Return the translated string for key.
        Unknown keys are are returned as a fallback.
        Placeholder are replaced via 'str.format_map'.
        """
        text = self._strings.get(key, key)
        if kwargs:
            try: text = text.format_map(kwargs)
            except (KeyError, ValueError): pass

        return text


# Singelton;
translator = Translator()


def tr(key: str, **kwargs) -> str:
    return translator.translate(key, **kwargs)