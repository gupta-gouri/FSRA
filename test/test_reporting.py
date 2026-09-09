from decimal import Decimal
from pathlib import Path
import pytest
import pandas as pd

from src.schemas.manifest import IngestionManifest, DocumentMetadata, StatementType
from src.schemas.statements import StandardFinancialStatement, StandardLineItem
from src.reporting.workpaper_exporter import build_audit_workbook, build_audit_pdf
from src.reporting.report_orchestrator import generate_full_audit_package


def create_sample_statements():
    bs_items = [
        StandardLineItem(standard_key="CashAndCashEquivalents", raw_description="Cash", cy_value=Decimal("100.0"), py_value=Decimal("80.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="AccountsReceivable", raw_description="AR", cy_value=Decimal("200.0"), py_value=Decimal("180.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="Inventories", raw_description="Inventories", cy_value=Decimal("150.0"), py_value=Decimal("135.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalCurrentAssets", raw_description="Total Current Assets", cy_value=Decimal("450.0"), py_value=Decimal("395.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="PropertyPlantAndEquipmentNet", raw_description="PP&E Net", cy_value=Decimal("350.0"), py_value=Decimal("300.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalAssets", raw_description="Total Assets", cy_value=Decimal("800.0"), py_value=Decimal("695.0"), row_type="TOTAL"),
        StandardLineItem(standard_key="AccountsPayable", raw_description="AP", cy_value=Decimal("100.0"), py_value=Decimal("90.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="ShortTermDebt", raw_description="ST Debt", cy_value=Decimal("50.0"), py_value=Decimal("40.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalCurrentLiabilities", raw_description="Total Current Liabilities", cy_value=Decimal("150.0"), py_value=Decimal("130.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="LongTermDebt", raw_description="LT Debt", cy_value=Decimal("200.0"), py_value=Decimal("180.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalLiabilities", raw_description="Total Liabilities", cy_value=Decimal("350.0"), py_value=Decimal("310.0"), row_type="TOTAL"),
        StandardLineItem(standard_key="RetainedEarnings", raw_description="Retained Earnings", cy_value=Decimal("250.0"), py_value=Decimal("200.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalStockholdersEquity", raw_description="Total Equity", cy_value=Decimal("450.0"), py_value=Decimal("385.0"), row_type="TOTAL"),
    ]

    is_items = [
        StandardLineItem(standard_key="Revenue", raw_description="Revenue", cy_value=Decimal("1000.0"), py_value=Decimal("900.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="CostOfGoodsSold", raw_description="COGS", cy_value=Decimal("600.0"), py_value=Decimal("540.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="GrossProfit", raw_description="Gross Profit", cy_value=Decimal("400.0"), py_value=Decimal("360.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="OperatingIncome", raw_description="Operating Income", cy_value=Decimal("200.0"), py_value=Decimal("170.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="DepreciationAndAmortizationExpense", raw_description="Depreciation", cy_value=Decimal("30.0"), py_value=Decimal("25.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="InterestExpense", raw_description="Interest Expense", cy_value=Decimal("20.0"), py_value=Decimal("15.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="EarningsBeforeTax", raw_description="EBT", cy_value=Decimal("180.0"), py_value=Decimal("155.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="IncomeTaxExpense", raw_description="Tax Expense", cy_value=Decimal("36.0"), py_value=Decimal("30.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="NetIncome", raw_description="Net Income", cy_value=Decimal("144.0"), py_value=Decimal("125.0"), row_type="TOTAL"),
    ]

    cfs_items = [
        StandardLineItem(standard_key="OperatingCashFlow", raw_description="Operating Cash Flow", cy_value=Decimal("150.0"), py_value=Decimal("130.0"), row_type="TOTAL"),
        StandardLineItem(standard_key="InvestingCashFlow", raw_description="Investing Cash Flow", cy_value=Decimal("-50.0"), py_value=Decimal("-40.0"), row_type="TOTAL"),
    ]

    return {
        StatementType.BALANCE_SHEET: StandardFinancialStatement(statement_type=StatementType.BALANCE_SHEET, line_items=bs_items),
        StatementType.INCOME_STATEMENT: StandardFinancialStatement(statement_type=StatementType.INCOME_STATEMENT, line_items=is_items),
        StatementType.CASH_FLOW_STATEMENT: StandardFinancialStatement(statement_type=StatementType.CASH_FLOW_STATEMENT, line_items=cfs_items),
    }


def create_sample_manifest():
    meta = DocumentMetadata(
        client_name="Acme Corp",
        period_ended="2026-12-31",
        currency="USD",
        scale="ONES",
    )
    return IngestionManifest(metadata=meta, sheets=[])


def test_build_audit_workbook_xlsxwriter(tmp_path):
    statements = create_sample_statements()
    manifest = create_sample_manifest()

    from src.verification.orchestrator import MathEngine
    engine = MathEngine(statements=statements, manifest=manifest)
    audit_report = engine.generate_structured_audit_report()

    # Add analytics sample dict
    from src.analytics.core_analytics import calculate_horizontal_vertical_analysis, calculate_financial_ratios, evaluate_relationship_disconnects
    yoy_df, cs_bs, cs_is = calculate_horizontal_vertical_analysis(statements[StatementType.BALANCE_SHEET], statements[StatementType.INCOME_STATEMENT])
    ratios_df = calculate_financial_ratios(statements[StatementType.BALANCE_SHEET], statements[StatementType.INCOME_STATEMENT])
    disc_df = evaluate_relationship_disconnects(statements)

    audit_report["analytics"] = {
        "yoy_variances": yoy_df.to_dict(orient="records"),
        "common_size_bs": cs_bs.to_dict(orient="records"),
        "ratios": ratios_df.to_dict(orient="records"),
        "relationship_disconnects": disc_df.to_dict(orient="records"),
    }

    output_file = tmp_path / "WP-514_Test_Workbook.xlsx"
    res_path = build_audit_workbook(audit_report, output_file)

    assert res_path.exists()
    assert res_path.stat().st_size > 0


def test_build_audit_pdf_reportlab(tmp_path):
    statements = create_sample_statements()
    manifest = create_sample_manifest()

    from src.verification.orchestrator import MathEngine
    engine = MathEngine(statements=statements, manifest=manifest)
    audit_report = engine.generate_structured_audit_report()

    output_file = tmp_path / "WP-514_Test_Report.pdf"
    res_path = build_audit_pdf(audit_report, output_file)

    assert res_path.exists()
    assert res_path.stat().st_size > 0


def test_generate_full_audit_package_e2e(tmp_path):
    statements = create_sample_statements()
    manifest = create_sample_manifest()
    out_dir = tmp_path / "audit_output"

    pkg = generate_full_audit_package(statements, manifest, output_dir=out_dir)

    assert "pdf_report" in pkg
    assert "excel_workbook" in pkg
    assert Path(pkg["pdf_report"]).exists()
    assert Path(pkg["excel_workbook"]).exists()
    assert Path(pkg["pdf_report"]).stat().st_size > 0
    assert Path(pkg["excel_workbook"]).stat().st_size > 0
