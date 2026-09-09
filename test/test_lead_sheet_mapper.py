import pytest
from src.extraction.lead_sheet_mapper import LEAD_SHEET_TAXONOMY, map_account_to_lead_sheet


@pytest.mark.parametrize(
    "acc_name,acc_num,expected_code,expected_fs",
    [
        ("Checking Bank Account", "1010", "A", "BALANCE_SHEET"),
        ("Trade Debtors", "1200", "C", "BALANCE_SHEET"),
        ("Raw Material Stock", "1300", "D", "BALANCE_SHEET"),
        ("Office Equipment", "1500", "F", "BALANCE_SHEET"),
        ("Vendor Trade Payables", "2010", "AA", "BALANCE_SHEET"),
        ("Senior Term Debt", "2500", "DD", "BALANCE_SHEET"),
        ("Equity Share Capital", "3000", "KK", "BALANCE_SHEET"),
        ("Gross Revenue", "4000", "10", "INCOME_STATEMENT"),
        ("Direct Materials COGS", "5000", "20", "INCOME_STATEMENT"),
        ("Office Rent and Salaries", "6000", "30", "INCOME_STATEMENT"),
    ],
)
def test_map_account_by_number_prefix(acc_name, acc_num, expected_code, expected_fs):
    """Test mapping accounts using GL 4-digit account number prefix heuristics."""
    code, name, fs = map_account_to_lead_sheet(acc_name, acc_num)
    assert code == expected_code
    assert fs == expected_fs


@pytest.mark.parametrize(
    "acc_name,expected_code,expected_fs",
    [
        ("Petty Cash Fund", "A", "BALANCE_SHEET"),
        ("Short-Term Treasury Bills", "B", "BALANCE_SHEET"),
        ("Customer Receivables", "C", "BALANCE_SHEET"),
        ("Allowance for Credit Losses", "C-1", "BALANCE_SHEET"),
        ("Finished Goods Inventory", "D", "BALANCE_SHEET"),
        ("Prepaid Insurance Premium", "E", "BALANCE_SHEET"),
        ("Factory Machinery", "F", "BALANCE_SHEET"),
        ("Accumulated Depreciation", "F-1", "BALANCE_SHEET"),
        ("Software Licenses Capitalised", "G", "BALANCE_SHEET"),
        ("Trade Payables", "AA", "BALANCE_SHEET"),
        ("Line of Credit Facility", "BB", "BALANCE_SHEET"),
        ("Accrued Payroll & Statutory Liabilities", "CC", "BALANCE_SHEET"),
        ("Senior Notes 2030", "DD", "BALANCE_SHEET"),
        ("Securities Premium Reserve", "KK", "BALANCE_SHEET"),
        ("Retained Earnings", "LL", "BALANCE_SHEET"),
        ("Turnover from Services", "10", "INCOME_STATEMENT"),
        ("Interest Income", "15", "INCOME_STATEMENT"),
        ("Cost of Goods Sold (COGS)", "20", "INCOME_STATEMENT"),
        ("Marketing & Advertising Expense", "30", "INCOME_STATEMENT"),
        ("Research and Development Costs", "40", "INCOME_STATEMENT"),
        ("Depreciation Expense", "50", "INCOME_STATEMENT"),
        ("Interest Expense & Loan Fees", "60", "INCOME_STATEMENT"),
        ("Income Tax Provision", "70", "INCOME_STATEMENT"),
    ],
)
def test_map_account_by_keywords(acc_name, expected_code, expected_fs):
    """Test mapping accounts based on keyword taxonomy when account number is missing."""
    code, name, fs = map_account_to_lead_sheet(acc_name, "")
    assert code == expected_code
    assert fs == expected_fs


def test_map_account_fallback():
    """Test fallback classification for unrecognized GL accounts."""
    code, name, fs = map_account_to_lead_sheet("Unclassified Miscellaneous Item", "")
    assert code == "OTH"
    assert name == "Other Miscellaneous Accounts"
    assert fs == "BALANCE_SHEET"


def test_lead_sheet_taxonomy_structure():
    """Test lead sheet taxonomy dictionary integrity."""
    assert "A" in LEAD_SHEET_TAXONOMY
    assert "AA" in LEAD_SHEET_TAXONOMY
    assert "10" in LEAD_SHEET_TAXONOMY
