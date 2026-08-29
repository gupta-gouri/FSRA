from decimal import Decimal
import pytest

from backend.src.schemas.manifest import StatementType
from backend.src.schemas.statements import StandardFinancialStatement, StandardLineItem
from backend.src.verification.assertions import run_complete_audit_suite


def _build_balanced_statements():
    """Helper to construct a fully consistent, balanced set of financial statements."""
    bs = StandardFinancialStatement(
        statement_type=StatementType.BALANCE_SHEET,
        entity_name="Test Entity",
        period_ended_cy="2023-12-31",
        currency="USD",
        scale=Decimal("1.0"),
        line_items=[
            StandardLineItem(standard_key="CashAndCashEquivalents", raw_description="Cash", cy_value=Decimal("100.0"), py_value=Decimal("80.0")),
            StandardLineItem(standard_key="AccountsReceivable", raw_description="AR", cy_value=Decimal("200.0"), py_value=Decimal("150.0")),
            StandardLineItem(standard_key="Inventories", raw_description="Inventory", cy_value=Decimal("150.0"), py_value=Decimal("120.0")),
            StandardLineItem(standard_key="PrepaidExpenses", raw_description="Prepaid", cy_value=Decimal("50.0"), py_value=Decimal("40.0")),
            StandardLineItem(standard_key="TotalCurrentAssets", raw_description="Total CA", cy_value=Decimal("500.0"), py_value=Decimal("390.0"), row_type="SUBTOTAL"),
            StandardLineItem(standard_key="PropertyPlantAndEquipmentNet", raw_description="PPE Net", cy_value=Decimal("500.0"), py_value=Decimal("450.0")),
            StandardLineItem(standard_key="IntangibleAssets", raw_description="Intangibles", cy_value=Decimal("0.0"), py_value=Decimal("0.0")),
            StandardLineItem(standard_key="TotalNonCurrentAssets", raw_description="Total NCA", cy_value=Decimal("500.0"), py_value=Decimal("450.0"), row_type="SUBTOTAL"),
            StandardLineItem(standard_key="TotalAssets", raw_description="Total Assets", cy_value=Decimal("1000.0"), py_value=Decimal("840.0"), row_type="TOTAL"),
            
            StandardLineItem(standard_key="AccountsPayable", raw_description="AP", cy_value=Decimal("100.0"), py_value=Decimal("90.0")),
            StandardLineItem(standard_key="ShortTermDebt", raw_description="ST Debt", cy_value=Decimal("50.0"), py_value=Decimal("50.0")),
            StandardLineItem(standard_key="AccruedLiabilities", raw_description="Accrued", cy_value=Decimal("50.0"), py_value=Decimal("40.0")),
            StandardLineItem(standard_key="TotalCurrentLiabilities", raw_description="Total CL", cy_value=Decimal("200.0"), py_value=Decimal("180.0"), row_type="SUBTOTAL"),
            StandardLineItem(standard_key="LongTermDebt", raw_description="LT Debt", cy_value=Decimal("300.0"), py_value=Decimal("250.0")),
            StandardLineItem(standard_key="TotalNonCurrentLiabilities", raw_description="Total NCL", cy_value=Decimal("300.0"), py_value=Decimal("250.0"), row_type="SUBTOTAL"),
            StandardLineItem(standard_key="TotalLiabilities", raw_description="Total Liab", cy_value=Decimal("500.0"), py_value=Decimal("430.0"), row_type="TOTAL"),
            
            StandardLineItem(standard_key="CommonStock", raw_description="Stock", cy_value=Decimal("200.0"), py_value=Decimal("200.0")),
            StandardLineItem(standard_key="AdditionalPaidInCapital", raw_description="APIC", cy_value=Decimal("100.0"), py_value=Decimal("100.0")),
            StandardLineItem(standard_key="RetainedEarnings", raw_description="Retained Earnings", cy_value=Decimal("200.0"), py_value=Decimal("110.0")),
            StandardLineItem(standard_key="AccumulatedOtherComprehensiveIncome", raw_description="AOCI", cy_value=Decimal("0.0"), py_value=Decimal("0.0")),
            StandardLineItem(standard_key="TotalStockholdersEquity", raw_description="Total Equity", cy_value=Decimal("500.0"), py_value=Decimal("410.0"), row_type="TOTAL"),
        ],
    )

    is_stmt = StandardFinancialStatement(
        statement_type=StatementType.INCOME_STATEMENT,
        entity_name="Test Entity",
        period_ended_cy="2023-12-31",
        line_items=[
            StandardLineItem(standard_key="Revenue", raw_description="Revenue", cy_value=Decimal("1000.0"), py_value=Decimal("800.0")),
            StandardLineItem(standard_key="CostOfGoodsSold", raw_description="COGS", cy_value=Decimal("-600.0"), py_value=Decimal("-480.0")),
            StandardLineItem(standard_key="GrossProfit", raw_description="Gross Profit", cy_value=Decimal("400.0"), py_value=Decimal("320.0"), row_type="SUBTOTAL"),
            StandardLineItem(standard_key="SellingGeneralAndAdministrative", raw_description="SGA", cy_value=Decimal("-200.0"), py_value=Decimal("-160.0")),
            StandardLineItem(standard_key="OperatingExpenses", raw_description="Opex", cy_value=Decimal("200.0"), py_value=Decimal("160.0"), row_type="SUBTOTAL"),
            StandardLineItem(standard_key="OperatingIncome", raw_description="EBIT", cy_value=Decimal("200.0"), py_value=Decimal("160.0"), row_type="SUBTOTAL"),
            StandardLineItem(standard_key="InterestExpense", raw_description="Interest", cy_value=Decimal("-50.0"), py_value=Decimal("-40.0")),
            StandardLineItem(standard_key="IncomeTaxExpense", raw_description="Taxes", cy_value=Decimal("-60.0"), py_value=Decimal("-50.0")),
            StandardLineItem(standard_key="NetIncome", raw_description="Net Income", cy_value=Decimal("90.0"), py_value=Decimal("70.0"), row_type="TOTAL"),
        ],
    )

    cfs = StandardFinancialStatement(
        statement_type=StatementType.CASH_FLOW_STATEMENT,
        entity_name="Test Entity",
        period_ended_cy="2023-12-31",
        line_items=[
            StandardLineItem(standard_key="OperatingCashFlow", raw_description="OCF", cy_value=Decimal("120.0")),
            StandardLineItem(standard_key="InvestingCashFlow", raw_description="ICF", cy_value=Decimal("-50.0")),
            StandardLineItem(standard_key="FinancingCashFlow", raw_description="FCF", cy_value=Decimal("-50.0")),
            StandardLineItem(standard_key="NetCashChange", raw_description="Net Cash Change", cy_value=Decimal("20.0")),
            StandardLineItem(standard_key="BeginningCash", raw_description="Beginning Cash", cy_value=Decimal("80.0")),
            StandardLineItem(standard_key="EndingCash", raw_description="Ending Cash", cy_value=Decimal("100.0")),
            StandardLineItem(standard_key="NetIncome", raw_description="CF Net Income", cy_value=Decimal("90.0")),
        ],
    )

    return {
        StatementType.BALANCE_SHEET: bs,
        StatementType.INCOME_STATEMENT: is_stmt,
        StatementType.CASH_FLOW_STATEMENT: cfs,
    }


def test_run_complete_audit_suite_all_pass():
    """Test executing full 28-rule audit suite on balanced statements."""
    statements = _build_balanced_statements()
    flags = run_complete_audit_suite(statements)

    assert len(flags) >= 20
    for flag in flags:
        # Critical rules like MATH_01, MATH_02, TIEOUT_01, TIEOUT_02 should pass
        if flag["rule_id"] in ["MATH_01", "MATH_02", "MATH_04", "TIEOUT_01", "TIEOUT_02"]:
            assert flag["status"] == "PASS", f"Rule {flag['rule_id']} failed unexpectedly: {flag}"


def test_math_01_equilibrium_failure():
    """Test MATH_01 Balance Sheet Equilibrium failure detection."""
    statements = _build_balanced_statements()
    # Intentionally corrupt Total Assets
    statements[StatementType.BALANCE_SHEET].line_items[8].cy_value = Decimal("9999.0")

    flags = run_complete_audit_suite(statements)
    math01_flag = next(f for f in flags if f["rule_id"] == "MATH_01")

    assert math01_flag["status"] == "FAIL"
    assert math01_flag["severity"] == "CRITICAL"
