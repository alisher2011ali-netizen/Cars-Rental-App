# coding=utf-8
"""
Разные отдельностоящие функции, которые используются в других модулях
"""

import re
from decimal import Decimal
from typing import *
from typing import TypeVar

import unidecode

from parsing import exceptions


def get_decimal_from_money(
    money_str: str, process_no_sign_as_negative=False
) -> Decimal:
    """
    Converts string, representing money to a Decimal.
    If process_no_sign_as_negative is set to True, then a number will be negative in case no leading sign is available

    Example:
    get_decimal_from_money('1 189,40', True) -> -1189.4
    """

    money_str = unidecode.unidecode(money_str)
    money_str = money_str.replace(" ", "")
    money_str = money_str.replace(",", ".")

    leading_plus = False
    if money_str[0] == "+":
        leading_plus = True

    money_decimal = Decimal(money_str)

    if process_no_sign_as_negative and not leading_plus:
        money_decimal = -1 * money_decimal

    return money_decimal


def split_Sberbank_line(line: str) -> List[str]:
    """
    Разделяем Сбербанковсую строчку на кусочки данных. Разделяем используя symbol TAB
    """
    line_parts = re.split(r"\t", line)
    line_parts = list(filter(None, line_parts))
    return line_parts
