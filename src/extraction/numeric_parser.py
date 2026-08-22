import re
from decimal import Decimal, InvalidOperation
from typing import Any, Optional


def parse_financial_number(val: Any) -> Optional[Decimal]:
    """
    Parses financial string/numeric inputs into Decimal values.
    Handles currency symbols, commas, negative numbers formatted as (100) or -100,
    and null/empty strings.
    """
    if val is None:
        return None

    if isinstance(val, (int, float, Decimal)):
        if isinstance(val, float):
            return Decimal(str(val))
        return Decimal(val)

    text = str(val).strip()
    if not text or text in ["-", "—", "N/A", "n/a", "nil", "null"]:
        return None

    # Check for negative in parentheses: '(1,234.50)' -> '-1234.50'
    is_negative = False
    if text.startswith("(") and text.endswith(")"):
        is_negative = True
        text = text[1:-1].strip()
    elif text.startswith("-"):
        is_negative = True
        text = text[1:].strip()

    # Strip currency symbols, commas, spaces
    cleaned = re.sub(r"[^\d\.]", "", text)
    if not cleaned:
        return None

    try:
        dec = Decimal(cleaned)
        return -dec if is_negative else dec
    except InvalidOperation:
        return None
