from decimal import Decimal
import pytest
from backend.src.extraction.numeric_parser import parse_financial_number


@pytest.mark.parametrize(
    "val,expected",
    [
        (100, Decimal("100")),
        (12.34, Decimal("12.34")),
        (Decimal("500.25"), Decimal("500.25")),
        ("1,000", Decimal("1000")),
        ("$1,234.56", Decimal("1234.56")),
        ("₹5,00,000", Decimal("500000")),
        ("(500.00)", Decimal("-500.00")),
        ("-250.50", Decimal("-250.50")),
        ("-", None),
        ("—", None),
        ("N/A", None),
        ("", None),
        (None, None),
        ("Invalid String", None),
    ],
)
def test_parse_financial_number(val, expected):
    """Test parsing strings, numbers, floats, currency formats, and edge cases to Decimal."""
    assert parse_financial_number(val) == expected
