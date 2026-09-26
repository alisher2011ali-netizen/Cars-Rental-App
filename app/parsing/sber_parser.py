from typing import Any

from parsing import exceptions, extractors
from parsing.extractor import Extractor
from parsing.extractors_generic import determine_extractor_auto


def parse_sber_text_to_dict(
    input_txt_file_name: str, format: str = "auto"
) -> list[dict[str, Any]]:
    """Parse Sberbank text statement into a list of structured transaction dictionaries.

    Args:
        input_txt_file_name (str): Filesystem path to the pre-extracted text statement file.
        format (str): Targeted parser class name or 'auto' for automatic heuristic detection. Defaults to 'auto'.

    Returns:
        list[dict[str, Any]]: Extracted transaction records represented as key-value pairs.

    Raises:
        UserInputError: If the specified format does not match any registered extractor class.
    """
    with open(input_txt_file_name, encoding="utf8") as file:
        file_text = file.read()

    extractor_type: type

    if format == "auto":
        extractor_type = determine_extractor_auto(file_text)
    else:
        # Match explicit extractor class by string identifier across registered parser plugins
        for extractor in extractors.extractors_list:
            if extractor.__name__ == format:
                extractor_type = extractor
                break
        else:
            raise exceptions.UserInputError(f"Задан неизвестный формат {format}")

    actual_extractor: Extractor = extractor_type(file_text)

    individual_entries = actual_extractor.get_entries()

    return individual_entries
