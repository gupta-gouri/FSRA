from decimal import Decimal
import pytest

from src.schemas.manifest import DocumentMetadata, IngestionManifest, StatementType
from src.schemas.statements import StandardFinancialStatement, StandardLineItem
from src.verification.orchestrator import MathEngine


def test_math_engine_audit_report():
    """Test MathEngine execution and structured audit report generation."""
    manifest = IngestionManifest(
        metadata=DocumentMetadata(
            client_name="Audit Client Inc.",
            period_ended="2023-12-31",
            currency="USD",
        )
    )

    bs = StandardFinancialStatement(
        statement_type=StatementType.BALANCE_SHEET,
        entity_name="Audit Client Inc.",
        line_items=[
            StandardLineItem(standard_key="CashAndCashEquivalents", cy_value=Decimal("100.0")),
            StandardLineItem(standard_key="AccountsReceivable", cy_value=Decimal("200.0")),
            StandardLineItem(standard_key="TotalCurrentAssets", cy_value=Decimal("300.0")),
            StandardLineItem(standard_key="PropertyPlantAndEquipmentNet", cy_value=Decimal("700.0")),
            StandardLineItem(standard_key="TotalNonCurrentAssets", cy_value=Decimal("700.0")),
            StandardLineItem(standard_key="TotalAssets", cy_value=Decimal("1000.0")),
            StandardLineItem(standard_key="AccountsPayable", cy_value=Decimal("200.0")),
            StandardLineItem(standard_key="TotalCurrentLiabilities", cy_value=Decimal("200.0")),
            StandardLineItem(standard_key="LongTermDebt", cy_value=Decimal("300.0")),
            StandardLineItem(standard_key="TotalNonCurrentLiabilities", cy_value=Decimal("300.0")),
            StandardLineItem(standard_key="TotalLiabilities", cy_value=Decimal("500.0")),
            StandardLineItem(standard_key="CommonStock", cy_value=Decimal("200.0")),
            StandardLineItem(standard_key="RetainedEarnings", cy_value=Decimal("300.0")),
            StandardLineItem(standard_key="TotalStockholdersEquity", cy_value=Decimal("500.0")),
        ],
    )

    is_stmt = StandardFinancialStatement(
        statement_type=StatementType.INCOME_STATEMENT,
        entity_name="Audit Client Inc.",
        line_items=[
            StandardLineItem(standard_key="Revenue", cy_value=Decimal("1000.0")),
            StandardLineItem(standard_key="CostOfGoodsSold", cy_value=Decimal("600.0")),
            StandardLineItem(standard_key="GrossProfit", cy_value=Decimal("400.0")),
            StandardLineItem(standard_key="OperatingIncome", cy_value=Decimal("200.0")),
            StandardLineItem(standard_key="NetIncome", cy_value=Decimal("150.0")),
        ],
    )

    cfs = StandardFinancialStatement(
        statement_type=StatementType.CASH_FLOW_STATEMENT,
        entity_name="Audit Client Inc.",
        line_items=[
            StandardLineItem(standard_key="OperatingCashFlow", cy_value=Decimal("150.0")),
            StandardLineItem(standard_key="BeginningCash", cy_value=Decimal("0.0")),
            StandardLineItem(standard_key="NetCashChange", cy_value=Decimal("100.0")),
            StandardLineItem(standard_key="EndingCash", cy_value=Decimal("100.0")),
            StandardLineItem(standard_key="NetIncome", cy_value=Decimal("150.0")),
        ],
    )

    statements = {
        StatementType.BALANCE_SHEET: bs,
        StatementType.INCOME_STATEMENT: is_stmt,
        StatementType.CASH_FLOW_STATEMENT: cfs,
    }

    engine = MathEngine(statements=statements, manifest=manifest)
    report = engine.generate_structured_audit_report()

    assert "engagement" in report
    assert report["engagement"]["client_name"] == "Audit Client Inc."
    assert "conclusion" in report
    assert "overall_status" in report["conclusion"]
    assert "procedures" in report
    assert len(report["procedures"]) > 0
