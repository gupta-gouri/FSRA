import pytest
from src.extraction.taxonomy import TAXONOMY_MAP, normalize_line_item_key


@pytest.mark.parametrize(
    "raw_desc,expected_key",
    [
        ("Cash and cash equivalents", "CashAndCashEquivalents"),
        ("1. Net Sales", "Revenue"),
        ("Trade Debtors", "AccountsReceivable"),
        ("Inventories [1]", "Inventories"),
        ("Property, Plant and Equipment (net)", "PropertyPlantAndEquipmentNet"),
        ("Total Current Assets Subtotal", "TotalCurrentAssets"),
        ("Trade Creditors", "AccountsPayable"),
        ("Long Term Borrowings", "LongTermDebt"),
        ("Retained Earnings", "RetainedEarnings"),
        ("Cost of Goods Sold (COGS)", "CostOfGoodsSold"),
        ("Gross Profit", "GrossProfit"),
        ("SG&A Expenses", "SellingGeneralAndAdministrative"),
        ("Operating Income (EBIT)", "OperatingIncome"),
        ("Profit for the year", "NetIncome"),
        ("Net Cash from Operating Activities", "OperatingCashFlow"),
        ("Capital Expenditures", "CapitalExpenditures"),
        ("Closing Cash", "EndingCash"),
    ],
)
def test_normalize_line_item_key_known(raw_desc, expected_key):
    """Test taxonomy normalization for standard financial statement line items."""
    assert normalize_line_item_key(raw_desc) == expected_key


def test_normalize_line_item_key_formatting_cleanups():
    """Test stripping of leading indices and footnote references."""
    assert normalize_line_item_key("A. Cash and Bank Balances (Note 3)") == "CashAndCashEquivalents"
    assert normalize_line_item_key("12. Trade Payables [2]") == "AccountsPayable"


def test_normalize_line_item_key_fallback():
    """Test fallback to sanitized PascalCase string for unmapped line items."""
    assert normalize_line_item_key("Custom Project Reserve") == "CustomProjectReserve"
    assert normalize_line_item_key("Special Item (2023)") == "SpecialItem2023"


def test_taxonomy_map_structure():
    """Test taxonomy map integrity."""
    assert isinstance(TAXONOMY_MAP, dict)
    assert "Revenue" in TAXONOMY_MAP
    assert "TotalAssets" in TAXONOMY_MAP
