from parsing import exceptions, extractors
from parsing.extractor import Extractor
from parsing.extractors_generic import determine_extractor_auto


def parse_sber_text_to_dict(input_txt_file_name: str, format="auto") -> list[dict]:
    """
    Парсит текстовый файл выписки и возвращает список транзакций.
    """
    with open(input_txt_file_name, encoding="utf8") as file:
        file_text = file.read()

    extractor_type: type

    if format == "auto":
        extractor_type = determine_extractor_auto(file_text)
    else:
        for extractor in extractors.extractors_list:
            if extractor.__name__ == format:
                extractor_type = extractor
                break
        else:
            raise exceptions.UserInputError(f"Задан неизвестный формат {format}")

    actual_extractor: Extractor = extractor_type(file_text)

    individual_entries = actual_extractor.get_entries()

    return individual_entries
