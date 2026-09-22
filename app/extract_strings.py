import os
import re

# Регулярное выражение для поиска строк с русскими буквами внутри кавычек
# Ищет текст вида "Привет" или 'Добавить машину'
CYRILLIC_STR_PATTERN = re.compile(r"['\"]([^'\"]*[а-яА-ЯёЁ]+[^'\"]*)['\"]")


def extract_russian_strings(project_dir):
    localization_dict = {}
    found_count = 1

    print("🔍 Сканирование файлов проекта...")

    # Рекурсивно обходим все папки проекта
    for root, _, files in os.walk(project_dir):
        # Пропускаем папки виртуального окружения, гита и кэша, чтобы не собирать мусор
        if any(ignored in root for ignored in ["venv", ".git", "__pycache__", ".idea"]):
            continue

        for file in files:
            if file.endswith(".py") and file != "extract_strings.py":
                file_path = os.path.join(root, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        matches = CYRILLIC_STR_PATTERN.findall(line)
                        for match in matches:
                            # Очищаем строку от лишних пробелов по краям
                            text = match.strip()

                            # Если этого текста еще нет в нашем словаре локализации
                            if text not in localization_dict.values():
                                # Генерируем уникальный ключ для JSON (например: txt_1, txt_2)
                                key = f"txt_{found_count}"
                                localization_dict[key] = text
                                found_count += 1

                                print(
                                    f"📍 Найдено в {file} (строка {line_num}): '{text}' -> Ключ: {key}"
                                )

    # Создаем папку для локалей, если её нет
    os.makedirs("data/locales", exist_ok=True)

    # Сохраняем результат в ru.json
    output_path = "data/locales/ru.json"
    # with open(output_path, "w", encoding="utf-8") as json_file:
    #     json.dump(localization_dict, json_file, ensure_ascii=False, indent=4)

    print(f"\n🎉 Готово! Все строки сохранены в: {output_path}")
    print(f" Всего уникальных строк найдено: {len(localization_dict)}")


if __name__ == "__main__":
    # Запускаем скрипт в текущей директории
    current_directory = os.path.dirname(os.path.abspath(__file__))
    extract_russian_strings(current_directory)
