from decimal import Decimal
import pytest
from src.extraction.row_tagger import determine_row_type


def test_determine_row_type_total():
    """Test identifying primary master bottom-line TOTAL rows."""
    assert determine_row_type("Total Assets", Decimal("1000"), Decimal("900")) == "TOTAL"
    assert determine_row_type("Net Income", Decimal("500"), Decimal("400")) == "TOTAL"
    assert determine_row_type("Total Liabilities and Equity", Decimal("1000"), Decimal("900")) == "TOTAL"
    assert determine_row_type("Ending Cash and Cash Equivalents", Decimal("200"), Decimal("150")) == "TOTAL"


def test_determine_row_type_subtotal():
    """Test identifying group roll-up SUBTOTAL rows."""
    assert determine_row_type("Total Current Assets", Decimal("600"), Decimal("500")) == "SUBTOTAL"
    assert determine_row_type("Gross Profit", Decimal("400"), Decimal("350")) == "SUBTOTAL"
    assert determine_row_type("Total Operating Expenses", Decimal("200"), Decimal("180")) == "SUBTOTAL"
    assert determine_row_type("Net Cash provided by Operating Activities", Decimal("300"), Decimal("250")) == "SUBTOTAL"


def test_determine_row_type_header():
    """Test identifying section HEADER rows (description present with CY value but no PY value)."""
    assert determine_row_type("ASSETS", Decimal("100"), None) == "HEADER"
    assert determine_row_type("Current Liabilities:", Decimal("50"), None) == "HEADER"


def test_determine_row_type_line():
    """Test identifying standard operational transaction LINE rows."""
    assert determine_row_type("Cash and cash equivalents", Decimal("100"), Decimal("80")) == "LINE"
    assert determine_row_type("Accounts Receivable", Decimal("200"), Decimal("180")) == "LINE"
    assert determine_row_type("Revenues", Decimal("1000"), Decimal("900")) == "LINE"
