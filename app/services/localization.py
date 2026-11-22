import json
import logging
import os
from typing import Any

logger = logging.getLogger()


class Localization:
    """Manage dynamic application localization and currency settings via JSON assets."""

    def __init__(
        self,
        default_lang: str | None = None,
        default_currency: str | None = None,
    ) -> None:
        self.strings = {}
        self.language = default_lang or "ru"
        self.currency = default_currency or "₽"
        self.load_lang(self.language)

    def load_lang(self, lang_code: str) -> None:
        """Load localized translation mappings from the corresponding JSON asset file."""

        current_dir = os.path.dirname(os.path.abspath(__file__))

        file_path = os.path.join(
            current_dir, "..", "assets", "locales", f"{lang_code}.json"
        )

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                self.strings = json.load(f)
        else:
            logger.warning(
                f"⚠ Localization file for '{lang_code}' not found. Using empty strings."
            )
            self.strings = {}

    def __getattr__(self, key: str) -> Any:
        return self.strings.get(key, key)


localization = Localization()
