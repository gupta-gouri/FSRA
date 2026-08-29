from decimal import Decimal
import pytest

from backend.src.schemas.manifest import StatementType
from backend.src.schemas.statements import StandardFinancialStatement, StandardLineItem
from backend.src.verification.guardrails import run_input_guardrails_suite


def test_run_input_guardrails_suite_pass():
    """Test guardrail checks pass for valid financial statements."""
    bs = StandardFinancialStatement(
        statement_type=StatementType.BALANCE_SHEET,
        line_items=[
            StandardLineItem(standard_key="TotalAssets", cy_value=Decimal("1000.0")),
            StandardLineItem(standard_key="TotalStockholdersEquity", cy_value=Decimal("500.0")),
            StandardLineItem(standard_key="CashAndCashEquivalents", cy_value=Decimal("100.0")),
        ],
    )
    is_stmt = StandardFinancialStatement(
        statement_type=StatementType.INCOME_STATEMENT,
        line_items=[
            StandardLineItem(standard_key="Revenue", cy_value=Decimal("500.0")),
            StandardLineItem(standard_key="CostOfGoodsSold", cy_value=Decimal("300.0")),
            StandardLineItem(standard_key="NetIncome", cy_value=Decimal("50.0")),
        ],
    )
    cfs = StandardFinancialStatement(
        statement_type=StatementType.CASH_FLOW_STATEMENT,
        line_items=[
            StandardLineItem(standard_key="OperatingCashFlow", cy_value=Decimal("60.0")),
            StandardLineItem(standard_key="EndingCash", cy_value=Decimal("100.0")),
        ],
    )

    statements = {
        StatementType.BALANCE_SHEET: bs,
        StatementType.INCOME_STATEMENT: is_stmt,
        StatementType.CASH_FLOW_STATEMENT: cfs,
    }

    results = run_input_guardrails_suite(statements)

    assert len(results) == 16
    for g in results:
        assert g["status"] in ("PASS", "WARNING")


def test_run_input_guardrails_suite_failures():
    """Test guardrail checks flag negative assets and COGS exceeding revenue."""
    bs = StandardFinancialStatement(
        statement_type=StatementType.BALANCE_SHEET,
        line_items=[
            StandardLineItem(standard_key="TotalAssets", cy_value=Decimal("-100.0")),
            StandardLineItem(standard_key="TotalStockholdersEquity", cy_value=Decimal("500.0")),
        ],
    )
    is_stmt = StandardFinancialStatement(
        statement_type=StatementType.INCOME_STATEMENT,
        line_items=[
            StandardLineItem(standard_key="Revenue", cy_value=Decimal("100.0")),
            StandardLineItem(standard_key="CostOfGoodsSold", cy_value=Decimal("200.0")),
        ],
    )

    statements = {
        StatementType.BALANCE_SHEET: bs,
        StatementType.INCOME_STATEMENT: is_stmt,
    }

    results = run_input_guardrails_suite(statements)

    bs_guard = next(r for r in results if r["rule_id"] == "BS_GUARD_01")
    assert bs_guard["status"] == "WARNING"

    is_guard3 = next(r for r in results if r["rule_id"] == "IS_GUARD_03")
    assert is_guard3["status"] == "WARNING"
