import os

from parsing.pdf2txtev import pdf_2_txt_file
from parsing.sber_parser import parse_sber_text_to_dict


def process_sber_pdf(input_pdf_path: str) -> list[dict]:
    """Extract text from a PDF, parse it into transactions, and clean up.

    Args:
        input_pdf_path: The path to the target PDF file.

    Returns:
        list[dict]: A list of parsed transaction dictionaries.
    """
    if not input_pdf_path.lower().endswith(".pdf"):
        raise ValueError("Файл должен быть в формате PDF")

    tmp_txt_file_name = input_pdf_path.replace(".pdf", ".txt")

    try:
        pdf_2_txt_file(input_pdf_path, tmp_txt_file_name)

        transactions = parse_sber_text_to_dict(tmp_txt_file_name)

    finally:
        if os.path.exists(tmp_txt_file_name):
            os.remove(tmp_txt_file_name)

    return transactions
