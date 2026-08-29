"""
main.py
Single Main Entry Point for the Financial Statement Review & Audit System (FSRA).

Usage:
    python main.py
    python main.py sample_audit_input.xlsx
    python main.py path/to/statements.xlsx path/to/report.pdf --output_dir audit_output
"""

import argparse
import sys
from pathlib import Path
from typing import Dict

# Ensure project root directory is in sys.path
ROOT_DIR = Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from backend.src.schemas.manifest import StatementType
from backend.src.schemas.statements import StandardFinancialStatement
from backend.src.ingestion.orchestrator import ingest_sources
from backend.src.extraction.extractor import extract_statements_from_manifest
from backend.src.reporting.report_orchestrator import generate_full_audit_package


def create_sample_input_excel(file_path: Path):
    """Helper to generate sample input workbook if none provided."""
    bs_data = {
        "Line Item": [
            "Cash and Cash Equivalents",
            "Accounts Receivable",
            "Inventories",
            "Total Current Assets",
            "Property Plant and Equipment Net",
            "Total Assets",
            "Accounts Payable",
            "Short-Term Debt",
            "Total Current Liabilities",
            "Long-Term Debt",
            "Total Liabilities",
            "Common Stock",
            "Retained Earnings",
            "Total Stockholders Equity",
            "Total Liabilities & Equity"
        ],
        "CY (2026)": [
            120000.0, 250000.0, 180000.0, 550000.0, 450000.0, 1000000.0,
            120000.0, 60000.0, 180000.0, 250000.0, 430000.0,
            200000.0, 370000.0, 570000.0, 1000000.0
        ],
        "PY (2025)": [
            100000.0, 210000.0, 160000.0, 470000.0, 400000.0, 870000.0,
            110000.0, 50000.0, 160000.0, 230000.0, 390000.0,
            200000.0, 280000.0, 480000.0, 870000.0
        ]
    }

    is_data = {
        "Line Item": [
            "Revenue",
            "Cost of Goods Sold",
            "Gross Profit",
            "Selling General and Administrative",
            "Operating Income",
            "Depreciation and Amortization Expense",
            "Interest Expense",
            "Earnings Before Tax",
            "Income Tax Expense",
            "Net Income"
        ],
        "CY (2026)": [
            1500000.0, 900000.0, 600000.0, 300000.0, 300000.0,
            40000.0, 25000.0, 275000.0, 55000.0, 220000.0
        ],
        "PY (2025)": [
            1300000.0, 800000.0, 500000.0, 260000.0, 240000.0,
            35000.0, 20000.0, 220000.0, 44000.0, 176000.0
        ]
    }

    cfs_data = {
        "Line Item": [
            "Operating Cash Flow",
            "Capital Expenditures",
            "Investing Cash Flow",
            "Financing Cash Flow"
        ],
        "CY (2026)": [210000.0, -90000.0, -90000.0, -100000.0],
        "PY (2025)": [180000.0, -70000.0, -70000.0, -90000.0]
    }

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        pd.DataFrame(bs_data).to_excel(writer, sheet_name="Balance Sheet", index=False)
        pd.DataFrame(is_data).to_excel(writer, sheet_name="Income Statement", index=False)
        pd.DataFrame(cfs_data).to_excel(writer, sheet_name="Cash Flow Statement", index=False)


def main():
    parser = argparse.ArgumentParser(
        description="FSRA End-to-End Financial Statement Review & Audit System"
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input financial statement file path(s) (.xlsx, .xls, .xlsm, .pdf). Defaults to sample_audit_input.xlsx."
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        default="audit_output",
        help="Output directory to save PDF and Excel deliverables (default: audit_output)"
    )
    parser.add_argument(
        "--client_name",
        help="Override client / entity name in metadata"
    )
    parser.add_argument(
        "--period",
        help="Override period ended (e.g. FY2026)"
    )
    parser.add_argument(
        "--currency",
        help="Override currency code (e.g. USD, EUR, INR)"
    )
    parser.add_argument(
        "--scale",
        help="Override scale multiplier (ONES, THOUSANDS, MILLIONS, BILLIONS, LAKHS, CRORES)"
    )
    parser.add_argument(
        "--resolve_conflicts",
        action="store_true",
        help="Trigger automated conflict resolution for duplicate statements"
    )

    args = parser.parse_args()

    # Default to sample_audit_input.xlsx if no input files provided
    if not args.inputs:
        sample_file = ROOT_DIR / "sample_audit_input.xlsx"
        if not sample_file.exists():
            print("[*] Generating sample input file: sample_audit_input.xlsx...")
            create_sample_input_excel(sample_file)
        input_paths = [sample_file]
    else:
        input_paths = [Path(p) for p in args.inputs]

    out_dir = Path(args.output_dir)

    print("=" * 80)
    print(" FINANCIAL STATEMENT REVIEW & AUDIT SYSTEM (FSRA) ")
    print("=" * 80)
    print(f"[*] Input Files : {[p.name for p in input_paths]}")
    print(f"[*] Output Dir  : {out_dir.resolve()}")
    print("-" * 80)

    # -------------------------------------------------------------------------
    # STAGE 1: INGESTION & METADATA CLASSIFICATION
    # -------------------------------------------------------------------------
    print("[1/4] Running Stage 1: Ingesting & Classifying Files...")
    try:
        manifest = ingest_sources(
            file_paths=input_paths,
            resolve_conflicts=args.resolve_conflicts
        )
    except Exception as e:
        print(f"[!] Ingestion Error: {e}")
        sys.exit(1)

    # Apply metadata overrides or defaults if unspecified
    manifest.metadata.client_name = args.client_name or manifest.metadata.client_name or "Acme_Corp"
    manifest.metadata.period_ended = args.period or manifest.metadata.period_ended or "FY2026"
    manifest.metadata.currency = args.currency or manifest.metadata.currency or "USD"
    manifest.metadata.scale = args.scale or manifest.metadata.scale or "ONES"

    print(f"    [+] Entity Name : {manifest.metadata.client_name}")
    print(f"    [+] Period Ended: {manifest.metadata.period_ended}")
    print(f"    [+] Currency    : {manifest.metadata.currency}")
    print(f"    [+] Scale       : {manifest.metadata.scale}")
    print(f"    [+] Sheets Found: {len(manifest.sheets)}")

    # -------------------------------------------------------------------------
    # STAGE 2: STANDARDIZED EXTRACTION & TAXONOMY MAPPING
    # -------------------------------------------------------------------------
    print("\n[2/4] Running Stage 2: Extracting & Standardizing Statements...")
    raw_extracted = extract_statements_from_manifest(manifest, apply_scale=False)

    statements: Dict[StatementType, StandardFinancialStatement] = {}
    for st in StatementType:
        val = raw_extracted.get(st.value) or raw_extracted.get(st)
        if isinstance(val, StandardFinancialStatement):
            statements[st] = val
            print(f"    [+] Extracted {st.value}: {len(val.line_items)} line items")

    # -------------------------------------------------------------------------
    # STAGE 3, 4 & 5: VERIFICATION, ANALYTICS, FORENSICS & PACKAGE GENERATION
    # -------------------------------------------------------------------------
    print("\n[3/4] Running Stage 3 & 4: Executing 44 Audit Rules, 5 Forensics & Trend Engines...")
    print("[4/4] Running Stage 5: Generating Deliverable PDF & WP-514 Excel Workpaper...")

    try:
        results = generate_full_audit_package(
            statements=statements,
            manifest=manifest,
            output_dir=out_dir
        )
    except Exception as e:
        print(f"[!] Package Generation Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 80)
    print(" AUDIT PACKAGE GENERATION COMPLETED SUCCESSFULLY ")
    print("=" * 80)
    print(f"[*] Audit Gate Status   : {results['overall_status']}")
    print(f"[*] Audit Procedures Run : {results['procedures_passed']}")
    print(f"[*] Deliverable A (PDF)  : {Path(results['pdf_report']).resolve()}")
    print(f"[*] Deliverable B (XLSX) : {Path(results['excel_workbook']).resolve()}")
    print("=" * 80)
    print("\nYou can open the generated PDF and Excel files above to inspect the audit results!")


if __name__ == "__main__":
    main()
