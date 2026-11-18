import os
import pprint
import sys

from app.parsing.parser import process_sber_pdf


def run_test():
    # Путь к PDF файлу с выпиской
    # ВАЖНО: для теста возьми реальную выписку
    test_pdf_path = "test_statement.pdf"

    if not os.path.exists(test_pdf_path):
        print(f"Файл {test_pdf_path} не найден! Положи PDF-файл рядом со скриптом.")
        return

    print(f"Начинаем парсинг файла: {test_pdf_path}")
    print("-" * 40)

    try:
        transactions = process_sber_pdf(test_pdf_path)

        print(f"Успешно! Найдено транзакций: {len(transactions)}\n")
        print("Первые 5 операций из выписки:")
        pprint.pprint(transactions[:5], indent=4, width=100, sort_dicts=False)

    except Exception as e:
        print(f"Ошибка при парсинге: {e}")


if __name__ == "__main__":
    run_test()
