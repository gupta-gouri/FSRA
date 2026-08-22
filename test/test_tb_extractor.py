from decimal import Decimal
from src.extraction.tb_extractor import extract_trial_balance
from src.schemas.manifest import RawSheetPayload, StatementType


def test_extract_trial_balance_success():
    """Test extracting a balanced Trial Balance with debit and credit columns."""
    payload = RawSheetPayload(
        source_filename="tb.xlsx",
        sheet_name="Trial Balance",
        raw_grid=[
            ["Account Code", "Account Name", "Debit", "Credit"],
            ["1010", "Cash in Bank", "1000.00", "0.00"],
            ["1200", "Trade Debtors", "500.00", "0.00"],
            ["2010", "Trade Creditors", "0.00", "600.00"],
            ["3000", "Share Capital", "0.00", "900.00"],
            ["Total", "Total Balance", "1500.00", "1500.00"],  # Total row skipped
        ],
        detected_type=StatementType.TRIAL_BALANCE,
    )

    tb = extract_trial_balance(payload, client_name="ACME Corp", period_ended="2023-12-31")

    assert tb.entity_name == "ACME Corp"
    assert tb.period_ended == "2023-12-31"
    assert tb.total_debits == Decimal("1500.00")
    assert tb.total_credits == Decimal("1500.00")
    assert tb.is_balanced is True

    # Account list length (excluding total row)
    assert len(tb.accounts) == 4

    # Lead sheet roll-ups
    assert "A" in tb.lead_sheets
    assert tb.lead_sheets["A"].net_balance == Decimal("1000.00")
    assert tb.lead_sheets["A"].account_count == 1

    assert "C" in tb.lead_sheets
    assert tb.lead_sheets["C"].net_balance == Decimal("500.00")

    assert "AA" in tb.lead_sheets
    assert tb.lead_sheets["AA"].total_credit == Decimal("600.00")


def test_extract_trial_balance_ending_balance():
    """Test extracting Trial Balance with Net Ending Balance column."""
    payload = RawSheetPayload(
        source_filename="tb_ending.xlsx",
        sheet_name="General Ledger TB",
        raw_grid=[
            ["Account No", "Description", "Ending Balance"],
            ["1010", "Petty Cash", "200.00"],
            ["2010", "Accounts Payable", "-200.00"],
        ],
        detected_type=StatementType.TRIAL_BALANCE,
    )

    tb = extract_trial_balance(payload, client_name="Beta Inc")

    assert len(tb.accounts) == 2
    assert tb.accounts[0].ending_balance == Decimal("200.00")
    assert tb.accounts[1].ending_balance == Decimal("-200.00")


def test_extract_trial_balance_empty_grid():
    """Test extracting from empty grid payload returns empty StandardTrialBalance."""
    payload = RawSheetPayload(
        source_filename="empty.xlsx",
        sheet_name="Empty",
        raw_grid=[],
        detected_type=StatementType.TRIAL_BALANCE,
    )
    tb = extract_trial_balance(payload)
    assert len(tb.accounts) == 0
    assert tb.is_balanced is False
