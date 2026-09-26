import json
import os
from typing import Any


class Localization:
    """Manage dynamic application localization and currency settings via JSON assets."""

    def __init__(
        self,
        default_lang: str | None = None,
        default_currency: str | None = None,
    ) -> None:
        """Initialize localization configuration and load default translation strings.

        Args:
            default_lang (str | None): Target language code (e.g., 'ru', 'en'). Defaults to 'ru'.
            default_currency (str | None): Default ISO currency code. Defaults to 'RUB'.

        Returns:
            None: Initializes localization state.
        """
        self.strings = {}
        self.language = default_lang or "ru"
        self.currency = default_currency or "RUB"
        self.load_lang(self.language)

    def load_lang(self, lang_code: str) -> None:
        """Load localized translation mappings from the corresponding JSON asset file.

        Args:
            lang_code (str): Two-letter or regional ISO language code.

        Returns:
            None: Modifies the internal strings mapping in-place.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))

        file_path = os.path.join(
            current_dir, "..", "assets", "locales", f"{lang_code}.json"
        )

        print(f"DEBUG: Ищу файл перевода по пути: {file_path}")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                self.strings = json.load(f)
        else:
            print(
                f"⚠ Localization file for '{lang_code}' not found. Using empty strings."
            )
            self.strings = {}

    def __getattr__(self, key: str) -> Any:
        """Resolve missing attributes as localization dictionary lookups.

        Args:
            key (str): Translation identifier key being accessed.

        Returns:
            Any: The translated text string if found; otherwise, returns the key itself as a fallback.
        """
        # Return the key literal as fallback to keep UI functional even if a translation entry is missing
        return self.strings.get(key, key)


localization = Localization()
