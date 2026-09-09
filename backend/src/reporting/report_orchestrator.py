"""
src/reporting/report_orchestrator.py
Main entry point for Stage 5: compiles the audit report dictionary and writes out
both Deliverable A (.pdf) and Deliverable B (.xlsx).
"""

from pathlib import Path
from typing import Any, Dict
import pandas as pd

from src.verification.orchestrator import MathEngine
from src.schemas.manifest import IngestionManifest, StatementType
from src.schemas.statements import StandardFinancialStatement
from src.analytics.core_analytics import (
    calculate_horizontal_vertical_analysis,
    calculate_financial_ratios,
    evaluate_relationship_disconnects,
)
from src.analytics.forensics import (
    compute_altman_z_score,
    compute_beneish_m_score,
    compute_sloan_accrual_ratio,
    compute_dupont_roe_breakdown,
    compute_benfords_law_analysis,
)
from src.analytics.historical_analytics import HistoricalAnalyticsEngine
from src.reporting.workpaper_exporter import build_audit_workbook, build_audit_pdf, sanitize_filename


def generate_full_audit_package(
    statements: Dict[StatementType, StandardFinancialStatement],
    manifest: IngestionManifest,
    output_dir: Path = Path("audit_output")
) -> Dict[str, str]:
    """
    Stage 5 Orchestrator:
    1. Executes MathEngine (28 rules + 16 guardrails)
    2. Runs Analytics, Forensics & Historical Analytics
    3. Exports Deliverable A (ReportLab PDF) and Deliverable B (XlsxWriter XLSX)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    bs = statements.get(StatementType.BALANCE_SHEET)
    is_stmt = statements.get(StatementType.INCOME_STATEMENT)
    cfs = statements.get(StatementType.CASH_FLOW_STATEMENT)

    # 1. Run Math Engine
    engine = MathEngine(statements=statements, manifest=manifest)
    base_report = engine.generate_structured_audit_report()

    # 2. Run Analytics & Forensics
    yoy_df, cs_bs, cs_is = calculate_horizontal_vertical_analysis(bs, is_stmt)
    ratios_df = calculate_financial_ratios(bs, is_stmt)
    disconnects_df = evaluate_relationship_disconnects(statements)

    z_score = compute_altman_z_score(bs, is_stmt)
    m_score = compute_beneish_m_score(bs, is_stmt, cfs)
    sloan = compute_sloan_accrual_ratio(bs, is_stmt, cfs)
    dupont = compute_dupont_roe_breakdown(bs, is_stmt)
    benford = compute_benfords_law_analysis(statements)

    # 3. Build Historical Analytics Report
    def _get_v(stmt, key, col):
        if not stmt:
            return 0.0
        for item in stmt.line_items:
            if item.standard_key == key:
                val = getattr(item, col, None)
                return float(val) if val is not None else 0.0
        return 0.0

    py_rec = {
        "fiscal_year": 2025,
        "revenue": _get_v(is_stmt, "Revenue", "py_value"),
        "cogs": abs(_get_v(is_stmt, "CostOfGoodsSold", "py_value")),
        "gross_profit": _get_v(is_stmt, "GrossProfit", "py_value"),
        "opex": _get_v(is_stmt, "TotalOperatingExpenses", "py_value"),
        "operating_income": _get_v(is_stmt, "OperatingIncome", "py_value"),
        "depreciation_amortization": _get_v(is_stmt, "DepreciationAndAmortizationExpense", "py_value"),
        "tax_expense": abs(_get_v(is_stmt, "IncomeTaxExpense", "py_value")),
        "net_income": _get_v(is_stmt, "NetIncome", "py_value"),
        "cash": _get_v(bs, "CashAndCashEquivalents", "py_value"),
        "accounts_receivable": _get_v(bs, "AccountsReceivable", "py_value"),
        "inventory": _get_v(bs, "Inventories", "py_value"),
        "accounts_payable": _get_v(bs, "AccountsPayable", "py_value"),
        "ppe_net": _get_v(bs, "PropertyPlantAndEquipmentNet", "py_value"),
        "total_assets": _get_v(bs, "TotalAssets", "py_value"),
        "total_equity": _get_v(bs, "TotalStockholdersEquity", "py_value"),
        "operating_cash_flow": _get_v(cfs, "OperatingCashFlow", "py_value"),
        "capex": abs(_get_v(cfs, "CapitalExpenditures", "py_value")),
    }

    cy_rec = {
        "fiscal_year": 2026,
        "revenue": _get_v(is_stmt, "Revenue", "cy_value"),
        "cogs": abs(_get_v(is_stmt, "CostOfGoodsSold", "cy_value")),
        "gross_profit": _get_v(is_stmt, "GrossProfit", "cy_value"),
        "opex": _get_v(is_stmt, "TotalOperatingExpenses", "cy_value"),
        "operating_income": _get_v(is_stmt, "OperatingIncome", "cy_value"),
        "depreciation_amortization": _get_v(is_stmt, "DepreciationAndAmortizationExpense", "cy_value"),
        "tax_expense": abs(_get_v(is_stmt, "IncomeTaxExpense", "cy_value")),
        "net_income": _get_v(is_stmt, "NetIncome", "cy_value"),
        "cash": _get_v(bs, "CashAndCashEquivalents", "cy_value"),
        "accounts_receivable": _get_v(bs, "AccountsReceivable", "cy_value"),
        "inventory": _get_v(bs, "Inventories", "cy_value"),
        "accounts_payable": _get_v(bs, "AccountsPayable", "cy_value"),
        "ppe_net": _get_v(bs, "PropertyPlantAndEquipmentNet", "cy_value"),
        "total_assets": _get_v(bs, "TotalAssets", "cy_value"),
        "total_equity": _get_v(bs, "TotalStockholdersEquity", "cy_value"),
        "operating_cash_flow": _get_v(cfs, "OperatingCashFlow", "cy_value"),
        "capex": abs(_get_v(cfs, "CapitalExpenditures", "cy_value")),
    }

    hist_df = pd.DataFrame([py_rec, cy_rec])
    hist_engine = HistoricalAnalyticsEngine(hist_df)
    historical_report = hist_engine.generate_full_historical_report()

    # 4. Assemble Unified Audit Report Dictionary
    unified_report = dict(base_report)
    unified_report["analytics"] = {
        "yoy_variances": yoy_df.to_dict(orient="records"),
        "common_size_bs": cs_bs.to_dict(orient="records"),
        "common_size_is": cs_is.to_dict(orient="records"),
        "ratios": ratios_df.to_dict(orient="records"),
        "relationship_disconnects": disconnects_df.to_dict(orient="records"),
        "historical_analytics": historical_report,
        "forensics": {
            "altman_z": z_score,
            "beneish_m": m_score,
            "sloan_accruals": sloan,
            "dupont_roe": dupont,
            "benfords_law": benford
        }
    }

    client = sanitize_filename(manifest.metadata.client_name or "Client")
    period = sanitize_filename(manifest.metadata.period_ended or "FY2026")

    pdf_path = output_dir / f"WP-514_Audit_Report_{client}_{period}.pdf"
    xlsx_path = output_dir / f"WP-514_Supporting_Workbook_{client}_{period}.xlsx"

    # 5. Generate Deliverables
    build_audit_pdf(unified_report, pdf_path)
    build_audit_workbook(unified_report, xlsx_path)

    return {
        "pdf_report": str(pdf_path),
        "excel_workbook": str(xlsx_path),
        "overall_status": base_report["conclusion"]["overall_status"],
        "procedures_passed": f"{base_report['conclusion']['procedures_passed']} / {base_report['conclusion']['total_procedures_run']}"
    }