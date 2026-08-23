"""
src/reporting/workpaper_exporter.py
Compiles and generates the complete WP-514 Financial Statement Review Package:
  1. Multi-tab Formatted Excel Workpaper (.xlsx) via XlsxWriter
  2. Audit Review Workpaper Report (.pdf) via ReportLab
"""

from __future__ import annotations
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xlsxwriter

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Style Palette Hex Codes
NAVY = '#1F4E78'
NAVY2 = '#17365D'
BLUE = '#D9EAF7'
PALE = '#F5F8FC'
GRID = '#B8C6D1'
GREEN = '#E2F0D9'
AMBER = '#FCE4D6'
RED = '#F4CCCC'
GREY = '#E7E6E6'
WHITE = '#FFFFFF'
TEXT = '#243444'


# =========================================================================
# HELPER FORMATTING FUNCTIONS
# =========================================================================

def fmt_val(v: Any, decimals: int = 2) -> str:
    if v is None or v == '':
        return '-'
    if isinstance(v, bool):
        return 'Yes' if v else 'No'
    if isinstance(v, (int, float)):
        if float(v).is_integer():
            return f'{int(v):,}'
        return f'{v:,.{decimals}f}'
    return str(v)


def fmt_pct(v: Any) -> str:
    if v is None or v == '' or pd.isna(v):
        return '-'
    try:
        return f'{float(v):+.1f}%'
    except Exception:
        return str(v)


def fill_for_status(status: Any) -> str:
    s = str(status or '').upper()
    if s in {'PASS', 'CLEARED', 'HEALTHY', 'ON TARGET', 'RESOLVED', 'EXCEEDED'}:
        return GREEN
    if s in {'FLAGGED', 'WARNING', 'REVIEW REQUIRED', 'BELOW TARGET', 'OPEN'}:
        return AMBER
    if s in {'FAIL', 'CRITICAL', 'REJECTED'}:
        return RED
    return GREY


def sanitize_filename(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]+', '-', str(s or 'report')).strip('-') or 'report'


def _clean_val(v: Any, default: Any = '-') -> Any:
    if v is None or pd.isna(v):
        return default
    try:
        f = float(v)
        if pd.isna(f) or np.isinf(f):
            return default
    except (ValueError, TypeError):
        pass
    return v


# =========================================================================
# XLSXWRITER WORKBOOK BUILDER (DELIVERABLE B)
# =========================================================================

def build_audit_workbook(audit_report: Dict[str, Any], output_path: Path) -> Path:
    """Builds the complete 6-tab WP-514 XlsxWriter supporting workbook."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb = xlsxwriter.Workbook(str(output_path), {'nan_inf_to_errors': True})

    eng = audit_report.get('engagement', {})
    an = audit_report.get('analytics', {})
    findings = audit_report.get('findings', [])
    conc = audit_report.get('conclusion', {})

    # Shared Formats
    fmt_title = wb.add_format({
        'bg_color': NAVY, 'font_color': WHITE, 'bold': True, 'font_size': 14,
        'align': 'left', 'valign': 'vcenter'
    })
    fmt_section = wb.add_format({
        'bg_color': BLUE, 'font_color': NAVY2, 'bold': True, 'font_size': 11,
        'align': 'left', 'valign': 'vcenter'
    })
    fmt_th = wb.add_format({
        'bg_color': NAVY, 'font_color': WHITE, 'bold': True, 'font_size': 9,
        'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'border_color': GRID
    })
    fmt_cell = wb.add_format({
        'font_size': 9, 'valign': 'top', 'text_wrap': True, 'border': 1, 'border_color': GRID
    })
    fmt_cell_bold = wb.add_format({
        'font_size': 9, 'bold': True, 'valign': 'top', 'text_wrap': True, 'border': 1, 'border_color': GRID
    })
    fmt_cell_num = wb.add_format({
        'font_size': 9, 'valign': 'top', 'border': 1, 'border_color': GRID, 'num_format': '#,##0.00;[Red](#,##0.00);-'
    })
    fmt_cell_pct = wb.add_format({
        'font_size': 9, 'valign': 'top', 'border': 1, 'border_color': GRID, 'num_format': '0.0%'
    })
    fmt_meta_label = wb.add_format({'bold': True, 'font_color': NAVY2, 'font_size': 9})
    fmt_meta_val = wb.add_format({'font_size': 9})

    # Status Formats
    fmt_status_pass = wb.add_format({'bg_color': GREEN, 'font_color': '000000', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': GRID})
    fmt_status_warn = wb.add_format({'bg_color': AMBER, 'font_color': '000000', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': GRID})
    fmt_status_fail = wb.add_format({'bg_color': RED, 'font_color': '000000', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'border_color': GRID})

    def get_status_format(status: Any):
        s = str(status or '').upper()
        if s in {'PASS', 'CLEARED', 'HEALTHY', 'ON TARGET', 'RESOLVED', 'EXCEEDED'}:
            return fmt_status_pass
        if s in {'FLAGGED', 'WARNING', 'REVIEW REQUIRED', 'BELOW TARGET', 'OPEN'}:
            return fmt_status_warn
        return fmt_status_fail

    client_name = str(eng.get('client_name', 'CLIENT')).upper()

    # ---------------------------------------------------------
    # TAB 1: WP-514 Review (Summary & Procedures)
    # ---------------------------------------------------------
    ws1 = wb.add_worksheet('WP-514 Review')
    ws1.hide_gridlines(0)
    ws1.merge_range('A1:H1', 'WORKPAPER WP-514: FINANCIAL STATEMENT REVIEW', fmt_title)
    ws1.set_row(0, 28)

    meta_labels = [
        ('Client / Entity', eng.get('client_name')),
        ('Period End', eng.get('period')),
        ('Currency', eng.get('currency')),
        ('Scale', eng.get('scale')),
        ('Framework', eng.get('framework', 'US GAAP / IFRS')),
        ('Review Stage', eng.get('review_stage', 'FINAL'))
    ]
    r = 2
    for i in range(0, len(meta_labels), 2):
        (l1, v1), (l2, v2) = meta_labels[i:i + 2]
        ws1.write(r, 0, l1, fmt_meta_label)
        ws1.write(r, 1, v1 or '-', fmt_meta_val)
        ws1.write(r, 3, l2, fmt_meta_label)
        ws1.write(r, 4, v2 or '-', fmt_meta_val)
        r += 1

    r += 1
    ws1.merge_range(r, 0, r, 7, 'REVIEW STATUS', fmt_section)
    ws1.set_row(r, 22)
    r += 1

    headers_status = ['Audit Status', 'Total Procedures', 'Passed Procedures', 'Open Findings', 'Scale', 'Currency', 'Framework', 'Review Stage']
    for c_idx, h in enumerate(headers_status):
        ws1.write(r, c_idx, h, fmt_th)
    ws1.set_row(r, 25)
    r += 1

    status_val = conc.get('overall_status', 'UNKNOWN')
    ws1.write(r, 0, status_val, get_status_format(status_val))
    ws1.write(r, 1, conc.get('total_procedures_run', 0), fmt_cell_bold)
    ws1.write(r, 2, conc.get('procedures_passed', 0), fmt_cell_bold)
    ws1.write(r, 3, len(findings), fmt_cell_bold)
    ws1.write(r, 4, eng.get('scale', 'ONES'), fmt_cell)
    ws1.write(r, 5, eng.get('currency', 'USD'), fmt_cell)
    ws1.write(r, 6, eng.get('framework', 'US GAAP / IFRS'), fmt_cell)
    ws1.write(r, 7, eng.get('review_stage', 'FINAL'), fmt_cell)
    r += 2

    ws1.merge_range(r, 0, r, 7, 'FINANCIAL STATEMENT REVIEW & CONTROL PROCEDURES', fmt_section)
    ws1.set_row(r, 22)
    r += 1

    headers_proc = ['Step #', 'Category', 'Review Procedure / Control Test', 'Reference', 'Status', 'Issue / Exception', 'Resolution', 'Workpaper Note']
    for c_idx, h in enumerate(headers_proc):
        ws1.write(r, c_idx, h, fmt_th)
    ws1.set_row(r, 25)
    r += 1

    for p in audit_report.get('procedures', []):
        ws1.write(r, 0, p.get('step'), fmt_cell)
        ws1.write(r, 1, p.get('category'), fmt_cell)
        ws1.write(r, 2, p.get('procedure'), fmt_cell)
        ws1.write(r, 3, p.get('reference'), fmt_cell)
        st = p.get('status')
        ws1.write(r, 4, st, get_status_format(st))
        ws1.write(r, 5, p.get('issue') or '-', fmt_cell)
        ws1.write(r, 6, p.get('resolution') or '-', fmt_cell)
        ws1.write(r, 7, '', fmt_cell)
        r += 1

    r += 1
    ws1.merge_range(r, 0, r, 1, 'Audit Gate Conclusion', fmt_th)
    ws1.merge_range(r, 2, r, 7, f"{conc.get('overall_status', '-')} | {conc.get('text', '-')}", fmt_cell)
    ws1.set_row(r, 30)

    ws1.set_column('A:A', 10)
    ws1.set_column('B:B', 24)
    ws1.set_column('C:C', 55)
    ws1.set_column('D:D', 20)
    ws1.set_column('E:E', 15)
    ws1.set_column('F:F', 38)
    ws1.set_column('G:G', 40)
    ws1.set_column('H:H', 28)
    ws1.freeze_panes(9, 0)

    # ---------------------------------------------------------
    # TAB 2: Financial Analytics (YoY & Common-Size)
    # ---------------------------------------------------------
    ws2 = wb.add_worksheet('Financial Analytics')
    ws2.hide_gridlines(0)
    ws2.merge_range('A1:G1', f"{client_name} - FINANCIAL STATEMENT ANALYTICS", fmt_title)
    ws2.set_row(0, 28)

    ws2.write(1, 0, f"Period: {eng.get('period', '-')} | Currency / Scale: {eng.get('currency', '-')} / {eng.get('scale', '-')}", fmt_meta_val)

    r = 3
    yoy_items = an.get('yoy_variances', [])
    if yoy_items:
        ws2.merge_range(r, 0, r, 6, 'YEAR OVER YEAR HORIZONTAL VARIANCE (ANALYTICS 01 - 02 & FLAG 01)', fmt_section)
        ws2.set_row(r, 22)
        r += 1
        headers_yoy = ['Statement', 'Line Item', 'Prior Period', 'Current Period', 'Variance ($)', 'Variance (%)', 'Audit Action']
        for c_idx, h in enumerate(headers_yoy):
            ws2.write(r, c_idx, h, fmt_th)
        ws2.set_row(r, 25)
        r += 1

        for item in yoy_items:
            ws2.write(r, 0, item.get('statement', '-'), fmt_cell)
            ws2.write(r, 1, item.get('line_item', '-'), fmt_cell)
            ws2.write(r, 2, _clean_val(item.get('prior_period'), 0.0), fmt_cell_num)
            ws2.write(r, 3, _clean_val(item.get('current_period'), 0.0), fmt_cell_num)
            ws2.write(r, 4, _clean_val(item.get('dollar_change'), 0.0), fmt_cell_num)
            pct_val = item.get('pct_change', 0.0)
            ws2.write(r, 5, (pct_val / 100.0) if abs(pct_val or 0.0) > 1.0 else pct_val, fmt_cell_pct)
            act = item.get('audit_action', 'PASS')
            ws2.write(r, 6, act, get_status_format(act))
            r += 1
        r += 1

    cs_bs = an.get('common_size_bs', [])
    if cs_bs:
        ws2.merge_range(r, 0, r, 6, 'COMMON-SIZE BALANCE SHEET (% OF TOTAL ASSETS)', fmt_section)
        ws2.set_row(r, 22)
        r += 1
        headers_cs = ['Standard Key', 'Line Item', 'Value ($)', 'Common-Size (%)', '', '', '']
        for c_idx in range(4):
            ws2.write(r, c_idx, headers_cs[c_idx], fmt_th)
        ws2.set_row(r, 25)
        r += 1

        for item in cs_bs:
            ws2.write(r, 0, item.get('standard_key', '-'), fmt_cell)
            ws2.write(r, 1, item.get('line_item', '-'), fmt_cell)
            ws2.write(r, 2, _clean_val(item.get('value'), 0.0), fmt_cell_num)
            pct_val = item.get('common_size_bs_pct', 0.0)
            ws2.write(r, 3, (pct_val / 100.0) if abs(pct_val or 0.0) > 1.0 else pct_val, fmt_cell_pct)
            r += 1

    ws2.set_column('A:A', 22)
    ws2.set_column('B:B', 34)
    ws2.set_column('C:C', 18)
    ws2.set_column('D:D', 18)
    ws2.set_column('E:E', 18)
    ws2.set_column('F:F', 16)
    ws2.set_column('G:G', 20)
    ws2.freeze_panes(4, 0)

    # ---------------------------------------------------------
    # TAB 3: Ratio & Disconnect Analysis (11 Ratios + 6 Disconnect Rules)
    # ---------------------------------------------------------
    ws3 = wb.add_worksheet('Ratio & Disconnect Analysis')
    ws3.hide_gridlines(0)
    ws3.merge_range('A1:G1', f"{client_name} - RATIOS & RELATIONSHIP DISCONNECTS", fmt_title)
    ws3.set_row(0, 28)

    r = 3
    ratios = an.get('ratios', [])
    if ratios:
        ws3.merge_range(r, 0, r, 6, 'KEY FINANCIAL RATIOS ENGINE (11 RULES)', fmt_section)
        ws3.set_row(r, 22)
        r += 1
        headers_ratio = ['Rule ID', 'Category', 'Ratio / Metric', 'Formula', 'Value', 'Benchmark', 'Status']
        for c_idx, h in enumerate(headers_ratio):
            ws3.write(r, c_idx, h, fmt_th)
        ws3.set_row(r, 25)
        r += 1

        for ratio in ratios:
            ws3.write(r, 0, ratio.get('rule_id', '-'), fmt_cell)
            ws3.write(r, 1, ratio.get('category', '-'), fmt_cell)
            ws3.write(r, 2, ratio.get('ratio_name', '-'), fmt_cell)
            ws3.write(r, 3, ratio.get('formula', '-'), fmt_cell)
            ws3.write(r, 4, ratio.get('formatted', str(ratio.get('value', '-'))), fmt_cell_bold)
            ws3.write(r, 5, ratio.get('benchmark', '-'), fmt_cell)
            st = ratio.get('status', 'PASS')
            ws3.write(r, 6, st, get_status_format(st))
            r += 1
        r += 1

    rel = an.get('relationship_disconnects', [])
    if rel:
        ws3.merge_range(r, 0, r, 6, 'UNIVERSAL RELATIONSHIP DISCONNECT CHECKS (REL 01 - 06)', fmt_section)
        ws3.set_row(r, 22)
        r += 1
        headers_rel = ['Rule ID', 'Rule Name', 'Condition / Metric', 'Threshold', 'Status', 'Audit Implication', '']
        for c_idx in range(6):
            ws3.write(r, c_idx, headers_rel[c_idx], fmt_th)
        ws3.set_row(r, 25)
        r += 1

        for x in rel:
            ws3.write(r, 0, x.get('rule_id', '-'), fmt_cell)
            ws3.write(r, 1, x.get('rule_name', '-'), fmt_cell)
            ws3.write(r, 2, str(x.get('metric_value', '-')), fmt_cell)
            ws3.write(r, 3, str(x.get('threshold', '-')), fmt_cell)
            st = x.get('status', 'PASS')
            ws3.write(r, 4, st, get_status_format(st))
            ws3.write(r, 5, x.get('audit_implication', '-'), fmt_cell)
            r += 1

    ws3.set_column('A:A', 15)
    ws3.set_column('B:B', 30)
    ws3.set_column('C:C', 30)
    ws3.set_column('D:D', 40)
    ws3.set_column('E:E', 18)
    ws3.set_column('F:F', 55)
    ws3.freeze_panes(4, 0)

    # ---------------------------------------------------------
    # TAB 4: Historical Analysis (CAGR, Swings, CCC, Asset Intensity, FCFF)
    # ---------------------------------------------------------
    ws4 = wb.add_worksheet('Historical Analysis')
    ws4.hide_gridlines(0)
    ws4.merge_range('A1:G1', f"{client_name} - MULTI-YEAR HISTORICAL TREND ANALYTICS", fmt_title)
    ws4.set_row(0, 28)

    r = 3
    hist = an.get('historical_analytics', {})
    cagr_data = hist.get('cagr_metrics', {})
    if cagr_data:
        ws4.merge_range(r, 0, r, 6, 'COMPOUND ANNUAL GROWTH RATE (CAGR)', fmt_section)
        ws4.set_row(r, 22)
        r += 1
        ws4.write(r, 0, 'Metric Key', fmt_th)
        ws4.write(r, 1, 'CAGR (%)', fmt_th)
        ws4.set_row(r, 25)
        r += 1
        for k, v in cagr_data.items():
            ws4.write(r, 0, k.replace('_cagr', '').replace('_', ' ').title(), fmt_cell)
            cagr_v = _clean_val(v, default=None)
            ws4.write(r, 1, (cagr_v / 100.0) if cagr_v is not None else '-', fmt_cell_pct if cagr_v is not None else fmt_cell)
            r += 1
        r += 1

    swings = hist.get('margin_bps_swings', [])
    if swings:
        ws4.merge_range(r, 0, r, 6, 'BASIS POINTS (BPS) MARGIN SWINGS', fmt_section)
        ws4.set_row(r, 22)
        r += 1
        headers_swings = ['Fiscal Year', 'Gross Margin (%)', 'Gross Margin (bps swing)', 'Operating Margin (%)', 'Operating Margin (bps swing)', 'Net Margin (%)', 'Net Margin (bps swing)']
        for c_idx, h in enumerate(headers_swings):
            ws4.write(r, c_idx, h, fmt_th)
        ws4.set_row(r, 25)
        r += 1
        for row in swings:
            ws4.write(r, 0, str(row.get('fiscal_year', '-')), fmt_cell)
            gm = _clean_val(row.get('gross_margin_pct'), 0.0)
            ws4.write(r, 1, (gm / 100.0), fmt_cell_pct)
            ws4.write(r, 2, _clean_val(row.get('gross_margin_bps_swing'), '-'), fmt_cell)
            om = _clean_val(row.get('operating_margin_pct'), 0.0)
            ws4.write(r, 3, (om / 100.0), fmt_cell_pct)
            ws4.write(r, 4, _clean_val(row.get('operating_margin_bps_swing'), '-'), fmt_cell)
            nm = _clean_val(row.get('net_margin_pct'), 0.0)
            ws4.write(r, 5, (nm / 100.0), fmt_cell_pct)
            ws4.write(r, 6, _clean_val(row.get('net_margin_bps_swing'), '-'), fmt_cell)
            r += 1
        r += 1

    ccc_data = hist.get('working_capital_ccc_trends', [])
    if ccc_data:
        ws4.merge_range(r, 0, r, 6, 'MULTI-YEAR WORKING CAPITAL & CCC TRENDS', fmt_section)
        ws4.set_row(r, 22)
        r += 1
        headers_ccc = ['Fiscal Year', 'DIO (Days)', 'DSO (Days)', 'DPO (Days)', 'Net CCC (Days)']
        for c_idx, h in enumerate(headers_ccc):
            ws4.write(r, c_idx, h, fmt_th)
        ws4.set_row(r, 25)
        r += 1
        for row in ccc_data:
            ws4.write(r, 0, str(row.get('fiscal_year', '-')), fmt_cell)
            ws4.write(r, 1, row.get('dio_days', 0.0), fmt_cell_bold)
            ws4.write(r, 2, row.get('dso_days', 0.0), fmt_cell_bold)
            ws4.write(r, 3, row.get('dpo_days', 0.0), fmt_cell_bold)
            ws4.write(r, 4, row.get('ccc_net_days', 0.0), fmt_cell_bold)
            r += 1
        r += 1

    fcff_data = hist.get('fcff_historical', [])
    if fcff_data:
        ws4.merge_range(r, 0, r, 6, 'HISTORICAL FREE CASH FLOW TO FIRM (FCFF)', fmt_section)
        ws4.set_row(r, 22)
        r += 1
        headers_fcff = ['Fiscal Year', 'Operating Income', 'NOPAT', 'D&A', 'CapEx', 'Delta NWC', 'FCFF']
        for c_idx, h in enumerate(headers_fcff):
            ws4.write(r, c_idx, h, fmt_th)
        ws4.set_row(r, 25)
        r += 1
        for row in fcff_data:
            ws4.write(r, 0, str(row.get('fiscal_year', '-')), fmt_cell)
            ws4.write(r, 1, row.get('operating_income', 0.0), fmt_cell_num)
            ws4.write(r, 2, row.get('nopat', 0.0), fmt_cell_num)
            ws4.write(r, 3, row.get('depreciation_amortization', 0.0), fmt_cell_num)
            ws4.write(r, 4, row.get('capex', 0.0), fmt_cell_num)
            ws4.write(r, 5, row.get('delta_nwc', 0.0), fmt_cell_num)
            ws4.write(r, 6, row.get('fcff', 0.0), fmt_cell_num)
            r += 1

    ws4.set_column('A:A', 22)
    ws4.set_column('B:B', 22)
    ws4.set_column('C:C', 22)
    ws4.set_column('D:D', 22)
    ws4.set_column('E:E', 22)
    ws4.set_column('F:F', 22)
    ws4.set_column('G:G', 22)
    ws4.freeze_panes(4, 0)

    # ---------------------------------------------------------
    # TAB 5: Findings & Exceptions
    # ---------------------------------------------------------
    ws5 = wb.add_worksheet('Findings & Exceptions')
    ws5.hide_gridlines(0)
    ws5.merge_range('A1:H1', 'WP-514 FINDINGS, EXCEPTIONS & RECONCILIATION', fmt_title)
    ws5.set_row(0, 28)

    r = 3
    headers_find = ['Finding ID', 'Rule ID', 'Severity', 'Description', 'Expected', 'Actual', 'Difference', 'Recommended Action']
    for c_idx, h in enumerate(headers_find):
        ws5.write(r, c_idx, h, fmt_th)
    ws5.set_row(r, 25)
    r += 1

    if findings:
        for f in findings:
            ws5.write(r, 0, f.get('id', '-'), fmt_cell)
            ws5.write(r, 1, f.get('rule_id', '-'), fmt_cell)
            sev = f.get('severity', 'HIGH')
            ws5.write(r, 2, sev, get_status_format(sev))
            ws5.write(r, 3, f.get('description', '-'), fmt_cell)
            ws5.write(r, 4, f.get('expected', 0.0), fmt_cell_num)
            ws5.write(r, 5, f.get('actual', 0.0), fmt_cell_num)
            ws5.write(r, 6, f.get('difference', 0.0), fmt_cell_num)
            ws5.write(r, 7, f.get('resolution', '-'), fmt_cell)
            r += 1
    else:
        ws5.merge_range('A5:H6', 'No audit exceptions or findings were detected. All deterministic assertions passed cleanly.', fmt_cell_bold)

    ws5.set_column('A:A', 16)
    ws5.set_column('B:B', 16)
    ws5.set_column('C:C', 15)
    ws5.set_column('D:D', 48)
    ws5.set_column('E:E', 18)
    ws5.set_column('F:F', 18)
    ws5.set_column('G:G', 18)
    ws5.set_column('H:H', 55)
    ws5.freeze_panes(4, 0)

    # ---------------------------------------------------------
    # TAB 6: Supporting Forensics
    # ---------------------------------------------------------
    ws6 = wb.add_worksheet('Forensic Analytics')
    ws6.hide_gridlines(0)
    ws6.merge_range('A1:F1', 'FORENSIC AUDIT & STATISTICAL MODELS', fmt_title)
    ws6.set_row(0, 28)

    r = 3
    forensics = an.get('forensics', {})
    if forensics:
        ws6.merge_range(r, 0, r, 5, 'STATISTICAL & FORENSIC AUDIT MODELS', fmt_section)
        ws6.set_row(r, 22)
        r += 1
        headers_for = ['Forensic Model', 'Score / Value', 'Risk Level / Status', 'Threshold / Benchmark', 'Details / Implications', '']
        for c_idx in range(5):
            ws6.write(r, c_idx, headers_for[c_idx], fmt_th)
        ws6.set_row(r, 25)
        r += 1

        altman = forensics.get('altman_z', {})
        if altman:
            ws6.write(r, 0, 'Altman Z-Score (Distress Risk)', fmt_cell_bold)
            ws6.write(r, 1, str(altman.get('z_score', '-')), fmt_cell)
            ws6.write(r, 2, altman.get('risk_level', '-'), get_status_format(altman.get('risk_level')))
            ws6.write(r, 3, 'Safe: > 2.99, Grey: 1.81-2.99, Distress: < 1.81', fmt_cell)
            ws6.write(r, 4, altman.get('zone', '-'), fmt_cell)
            r += 1

        beneish = forensics.get('beneish_m', {})
        if beneish:
            ws6.write(r, 0, 'Beneish M-Score (Manipulation)', fmt_cell_bold)
            ws6.write(r, 1, str(beneish.get('m_score', '-')), fmt_cell)
            ws6.write(r, 2, 'FLAGGED' if 'FLAGGED' in str(beneish.get('status')) else 'PASS', get_status_format(beneish.get('status')))
            ws6.write(r, 3, 'Manipulation Threshold: > -1.78', fmt_cell)
            ws6.write(r, 4, str(beneish.get('status', '-')), fmt_cell)
            r += 1

        sloan = forensics.get('sloan_accruals', {})
        if sloan:
            ws6.write(r, 0, 'Sloan Accrual Ratio (Quality)', fmt_cell_bold)
            ws6.write(r, 1, str(sloan.get('sloan_accrual_ratio', '-')), fmt_cell)
            ws6.write(r, 2, sloan.get('earnings_quality', '-'), fmt_cell)
            ws6.write(r, 3, 'Safe Range: -10.0% to +10.0%', fmt_cell)
            ws6.write(r, 4, f"Accrual Dollar: ${sloan.get('accrual_dollar_value', 0):,}", fmt_cell)
            r += 1

    ws6.set_column('A:A', 28)
    ws6.set_column('B:B', 22)
    ws6.set_column('C:C', 25)
    ws6.set_column('D:D', 30)
    ws6.set_column('E:E', 15)
    ws6.set_column('F:F', 55)
    ws6.freeze_panes(4, 0)

    wb.close()
    return output_path


# =========================================================================
# REPORTLAB PDF BUILDER (DELIVERABLE A)
# =========================================================================

def _P(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text if text not in (None, '') else '-'), style)


def _build_pdf_table(rows: List[List[Any]], widths: List[float], header: bool = True, status_col: Optional[int] = None) -> Table:
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
    cmds = [
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor(GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.0),
    ]
    if header:
        cmds.extend([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ])
    for r in range(1 if header else 0, len(rows)):
        if r % 2 == 0:
            cmds.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor(PALE)))
        if status_col is not None:
            raw = rows[r][status_col]
            txt = raw.getPlainText() if hasattr(raw, 'getPlainText') else str(raw)
            cmds.append(('BACKGROUND', (status_col, r), (status_col, r), colors.HexColor(fill_for_status(txt))))
            cmds.append(('FONTNAME', (status_col, r), (status_col, r), 'Helvetica-Bold'))
    t.setStyle(TableStyle(cmds))
    return t


def build_audit_pdf(audit_report: Dict[str, Any], output_path: Path) -> Path:
    """Builds the Deliverable A landscape PDF Audit Tie-Outs & Review Report."""
    eng = audit_report.get('engagement', {})
    an = audit_report.get('analytics', {})
    findings = audit_report.get('findings', [])
    conc = audit_report.get('conclusion', {})

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=12 * mm,
        bottomMargin=13 * mm,
        title='WP-514 Financial Statement Review Workpaper'
    )

    ss = getSampleStyleSheet()
    body = ParagraphStyle('body', parent=ss['BodyText'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=colors.HexColor(TEXT))
    small = ParagraphStyle('small', parent=body, fontSize=6.8, leading=8.5)
    h = ParagraphStyle('h', parent=ss['Heading2'], fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=colors.HexColor(NAVY2), spaceBefore=8, spaceAfter=5)
    white = ParagraphStyle('white', parent=body, textColor=colors.white, fontSize=8, leading=10)
    card = ParagraphStyle('card', parent=body, fontName='Helvetica-Bold', fontSize=12, leading=14, alignment=TA_CENTER, textColor=colors.HexColor(NAVY2))
    cardlab = ParagraphStyle('cardlab', parent=body, fontSize=6.8, leading=8, alignment=TA_CENTER, textColor=colors.HexColor('#5A6773'))

    story = []

    # Banner Header
    banner = Table([
        [
            _P('<b>AUDIT WORKPAPER WP-514</b><br/><font size="9">Financial Statement Review & Verification</font>', ParagraphStyle('b', parent=white, fontSize=16, leading=20)),
            _P(f"<b>Client:</b> {eng.get('client_name', '-')}<br/><b>Period:</b> {eng.get('period', '-')}<br/><b>Currency / Scale:</b> {eng.get('currency', '-')} / {eng.get('scale', '-')}", white),
            _P(f"<b>Framework:</b> {eng.get('framework', '-')}<br/><b>Review Stage:</b> {eng.get('review_stage', '-')}<br/><b>Overall Status:</b> {conc.get('overall_status', '-')}", white)
        ]
    ], colWidths=[100 * mm, 82 * mm, 82 * mm])
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(NAVY)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.extend([banner, Spacer(1, 5)])

    # Summary Cards
    cards = [
        Table([[_P('PROCEDURES RUN', cardlab)], [_P(f"{conc.get('procedures_passed', 0)} / {conc.get('total_procedures_run', 0)}", card)]], colWidths=[62 * mm]),
        Table([[_P('GATE STATUS', cardlab)], [_P(conc.get('overall_status', '-'), card)]], colWidths=[62 * mm]),
        Table([[_P('OPEN FINDINGS', cardlab)], [_P(str(len(findings)), card)]], colWidths=[62 * mm]),
        Table([[_P('FRAMEWORK', cardlab)], [_P(eng.get('framework', 'US GAAP'), card)]], colWidths=[62 * mm]),
    ]
    ct = Table([cards], colWidths=[67 * mm] * 4)
    ct.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor(GRID)),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFCFE')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.extend([ct, Spacer(1, 5)])

    # Section 1: Review Procedures
    story.append(_P('1. FINANCIAL STATEMENT REVIEW & MECHANICAL AUDIT PROCEDURES (28 RULES)', h))
    proc_rows = [[_P(x, small) for x in ['#', 'Category', 'Review / Control Test', 'Ref', 'Status', 'Discrepancy / Issue', 'Resolution']]]
    for p in audit_report.get('procedures', []):
        proc_rows.append([
            _P(p.get('step'), small),
            _P(p.get('category'), small),
            _P(p.get('procedure'), small),
            _P(p.get('reference'), small),
            _P(p.get('status'), small),
            _P(p.get('issue') or '-', small),
            _P(p.get('resolution') or '-', small)
        ])
    story.extend([_build_pdf_table(proc_rows, [10 * mm, 38 * mm, 80 * mm, 24 * mm, 20 * mm, 50 * mm, 52 * mm], status_col=4), Spacer(1, 5)])

    # Section 2: Key Financial Ratios
    ratios = an.get('ratios', [])
    if ratios:
        story.append(_P('2. KEY FINANCIAL RATIOS ENGINE (11 RULES)', h))
        ratio_rows = [[_P(x, small) for x in ['Category', 'Ratio Name', 'Formula', 'Value', 'Benchmark', 'Status']]]
        for r in ratios:
            ratio_rows.append([
                _P(r.get('category'), small),
                _P(r.get('ratio_name'), small),
                _P(r.get('formula'), small),
                _P(r.get('formatted', str(r.get('value', '-'))), small),
                _P(r.get('benchmark'), small),
                _P(r.get('status'), small)
            ])
        story.extend([_build_pdf_table(ratio_rows, [35 * mm, 45 * mm, 85 * mm, 30 * mm, 45 * mm, 24 * mm], status_col=5), Spacer(1, 4)])

    # Section 3: Findings & Exceptions
    if findings:
        story.append(_P('3. AUDIT FINDINGS & EXCEPTIONS SCHEDULE', h))
        for f in findings:
            box = Table([
                [_P(f"<b>{f.get('id', '-')}</b> | Rule: <b>{f.get('rule_id', '-')}</b> | Severity: <b>{f.get('severity', '-')}</b> | Status: <b>{f.get('status', 'OPEN')}</b>", body)],
                [_P(f"<b>Description:</b> {f.get('description', '-')}", body)],
                [_P(f"<b>Expected:</b> {fmt_val(f.get('expected'))} &nbsp;&nbsp; <b>Actual:</b> {fmt_val(f.get('actual'))} &nbsp;&nbsp; <b>Difference:</b> {fmt_val(f.get('difference'))}", body)],
                [_P(f"<b>Recommended Action:</b> {f.get('resolution', '-')}", body)]
            ], colWidths=[274 * mm])
            box.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(GRID)),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(fill_for_status(f.get('severity')))),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.extend([box, Spacer(1, 3)])

    # Section 4: Audit Gate Conclusion
    story.append(_P('4. FINAL AUDIT OPINION & CONCLUSION', h))
    conc_rows = [
        [_P('Deterministic Audit Conclusion', body), _P(conc.get('overall_status', '-'), body), _P(conc.get('text', '-'), body)]
    ]
    story.append(_build_pdf_table(conc_rows, [45 * mm, 35 * mm, 194 * mm], header=False, status_col=1))

    def footer_callback(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor(NAVY))
        canvas.line(13 * mm, 10 * mm, 284 * mm, 10 * mm)
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(colors.HexColor('#667788'))
        canvas.drawString(13 * mm, 6.5 * mm, f"WP-514 Review Workpaper | {eng.get('client_name', '-')} | {eng.get('period', '-')}")
        canvas.drawRightString(284 * mm, 6.5 * mm, f'Page {document.page}')
        canvas.restoreState()

    doc.build(story, onFirstPage=footer_callback, onLaterPages=footer_callback)
    return output_path



# =========================================================================
# REPORTLAB PDF BUILDER (DELIVERABLE A)
# =========================================================================

def _P(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text if text not in (None, '') else '-'), style)


def _build_pdf_table(rows: List[List[Any]], widths: List[float], header: bool = True, status_col: Optional[int] = None) -> Table:
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
    cmds = [
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor(GRID)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.0),
    ]
    if header:
        cmds.extend([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ])
    for r in range(1 if header else 0, len(rows)):
        if r % 2 == 0:
            cmds.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor(PALE)))
        if status_col is not None:
            raw = rows[r][status_col]
            txt = raw.getPlainText() if hasattr(raw, 'getPlainText') else str(raw)
            cmds.append(('BACKGROUND', (status_col, r), (status_col, r), colors.HexColor(fill_for_status(txt))))
            cmds.append(('FONTNAME', (status_col, r), (status_col, r), 'Helvetica-Bold'))
    t.setStyle(TableStyle(cmds))
    return t


def build_audit_pdf(audit_report: Dict[str, Any], output_path: Path) -> Path:
    """Builds the Deliverable A landscape PDF Audit Tie-Outs & Review Report."""
    eng = audit_report.get('engagement', {})
    an = audit_report.get('analytics', {})
    findings = audit_report.get('findings', [])
    conc = audit_report.get('conclusion', {})

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=12 * mm,
        bottomMargin=13 * mm,
        title='WP-514 Financial Statement Review Workpaper'
    )

    ss = getSampleStyleSheet()
    body = ParagraphStyle('body', parent=ss['BodyText'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=colors.HexColor(TEXT))
    small = ParagraphStyle('small', parent=body, fontSize=6.8, leading=8.5)
    h = ParagraphStyle('h', parent=ss['Heading2'], fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=colors.HexColor(NAVY2), spaceBefore=8, spaceAfter=5)
    white = ParagraphStyle('white', parent=body, textColor=colors.white, fontSize=8, leading=10)
    card = ParagraphStyle('card', parent=body, fontName='Helvetica-Bold', fontSize=12, leading=14, alignment=TA_CENTER, textColor=colors.HexColor(NAVY2))
    cardlab = ParagraphStyle('cardlab', parent=body, fontSize=6.8, leading=8, alignment=TA_CENTER, textColor=colors.HexColor('#5A6773'))

    story = []

    # Banner Header
    banner = Table([
        [
            _P('<b>AUDIT WORKPAPER WP-514</b><br/><font size="9">Financial Statement Review & Verification</font>', ParagraphStyle('b', parent=white, fontSize=16, leading=20)),
            _P(f"<b>Client:</b> {eng.get('client_name', '-')}<br/><b>Period:</b> {eng.get('period', '-')}<br/><b>Currency / Scale:</b> {eng.get('currency', '-')} / {eng.get('scale', '-')}", white),
            _P(f"<b>Framework:</b> {eng.get('framework', '-')}<br/><b>Review Stage:</b> {eng.get('review_stage', '-')}<br/><b>Overall Status:</b> {conc.get('overall_status', '-')}", white)
        ]
    ], colWidths=[100 * mm, 82 * mm, 82 * mm])
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(NAVY)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.extend([banner, Spacer(1, 5)])

    # Summary Cards
    cards = [
        Table([[_P('PROCEDURES RUN', cardlab)], [_P(f"{conc.get('procedures_passed', 0)} / {conc.get('total_procedures_run', 0)}", card)]], colWidths=[62 * mm]),
        Table([[_P('GATE STATUS', cardlab)], [_P(conc.get('overall_status', '-'), card)]], colWidths=[62 * mm]),
        Table([[_P('OPEN FINDINGS', cardlab)], [_P(str(len(findings)), card)]], colWidths=[62 * mm]),
        Table([[_P('FRAMEWORK', cardlab)], [_P(eng.get('framework', 'US GAAP'), card)]], colWidths=[62 * mm]),
    ]
    ct = Table([cards], colWidths=[67 * mm] * 4)
    ct.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.4, colors.HexColor(GRID)),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFCFE')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.extend([ct, Spacer(1, 5)])

    # Section 1: Review Procedures
    story.append(_P('1. FINANCIAL STATEMENT REVIEW & MECHANICAL AUDIT PROCEDURES (28 RULES)', h))
    proc_rows = [[_P(x, small) for x in ['#', 'Category', 'Review / Control Test', 'Ref', 'Status', 'Discrepancy / Issue', 'Resolution']]]
    for p in audit_report.get('procedures', []):
        proc_rows.append([
            _P(p.get('step'), small),
            _P(p.get('category'), small),
            _P(p.get('procedure'), small),
            _P(p.get('reference'), small),
            _P(p.get('status'), small),
            _P(p.get('issue') or '-', small),
            _P(p.get('resolution') or '-', small)
        ])
    story.extend([_build_pdf_table(proc_rows, [10 * mm, 38 * mm, 80 * mm, 24 * mm, 20 * mm, 50 * mm, 52 * mm], status_col=4), Spacer(1, 5)])

    # Section 2: Key Financial Ratios
    ratios = an.get('ratios', [])
    if ratios:
        story.append(_P('2. KEY FINANCIAL RATIOS ENGINE (11 RULES)', h))
        ratio_rows = [[_P(x, small) for x in ['Category', 'Ratio Name', 'Formula', 'Value', 'Benchmark', 'Status']]]
        for r in ratios:
            ratio_rows.append([
                _P(r.get('category'), small),
                _P(r.get('ratio_name'), small),
                _P(r.get('formula'), small),
                _P(r.get('formatted', str(r.get('value', '-'))), small),
                _P(r.get('benchmark'), small),
                _P(r.get('status'), small)
            ])
        story.extend([_build_pdf_table(ratio_rows, [35 * mm, 45 * mm, 85 * mm, 30 * mm, 45 * mm, 24 * mm], status_col=5), Spacer(1, 4)])

    # Section 3: Findings & Exceptions
    if findings:
        story.append(_P('3. AUDIT FINDINGS & EXCEPTIONS SCHEDULE', h))
        for f in findings:
            box = Table([
                [_P(f"<b>{f.get('id', '-')}</b> | Rule: <b>{f.get('rule_id', '-')}</b> | Severity: <b>{f.get('severity', '-')}</b> | Status: <b>{f.get('status', 'OPEN')}</b>", body)],
                [_P(f"<b>Description:</b> {f.get('description', '-')}", body)],
                [_P(f"<b>Expected:</b> {fmt_val(f.get('expected'))} &nbsp;&nbsp; <b>Actual:</b> {fmt_val(f.get('actual'))} &nbsp;&nbsp; <b>Difference:</b> {fmt_val(f.get('difference'))}", body)],
                [_P(f"<b>Recommended Action:</b> {f.get('resolution', '-')}", body)]
            ], colWidths=[274 * mm])
            box.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(GRID)),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(fill_for_status(f.get('severity')))),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.extend([box, Spacer(1, 3)])

    # Section 4: Audit Gate Conclusion
    story.append(_P('4. FINAL AUDIT OPINION & CONCLUSION', h))
    conc_rows = [
        [_P('Deterministic Audit Conclusion', body), _P(conc.get('overall_status', '-'), body), _P(conc.get('text', '-'), body)]
    ]
    story.append(_build_pdf_table(conc_rows, [45 * mm, 35 * mm, 194 * mm], header=False, status_col=1))

    def footer_callback(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor(NAVY))
        canvas.line(13 * mm, 10 * mm, 284 * mm, 10 * mm)
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(colors.HexColor('#667788'))
        canvas.drawString(13 * mm, 6.5 * mm, f"WP-514 Review Workpaper | {eng.get('client_name', '-')} | {eng.get('period', '-')}")
        canvas.drawRightString(284 * mm, 6.5 * mm, f'Page {document.page}')
        canvas.restoreState()

    doc.build(story, onFirstPage=footer_callback, onLaterPages=footer_callback)
    return output_path