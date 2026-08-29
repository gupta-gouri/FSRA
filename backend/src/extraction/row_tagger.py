import re
from typing import List, Optional
from decimal import Decimal

TOTAL_SIGNATURES = [
    # --- Balance Sheet Master Totals ---
    "total assets",
    "total liabilities and equity",
    "total liabilities & equity",
    "total liabilities and stockholders' equity",
    "total liabilities & stockholders' equity",
    "total liabilities and shareholders' equity",
    "total liabilities & shareholders' equity",
    "total liabilities and members' equity",
    "total equity and liabilities",
    "total stockholders' equity",
    "total stockholders equity",
    "total shareholders' equity",
    "total shareholders equity",
    "total equity",
    "total members' equity",
    "total partners' capital",
    "total liabilities and partners' capital",
    
    # --- Income Statement Bottom Lines ---
    "net income",
    "net income (loss)",
    "net income / (loss)",
    "net loss",
    "net earnings",
    "net profit",
    "net profit / (loss)",
    "net profit for the year",
    "net profit for the period",
    "profit for the year",
    "profit / (loss) for the year",
    "profit attributable to equity holders",
    "total comprehensive income",
    "total comprehensive income for the year",
    "comprehensive income attributable to shareholders",
    
    # --- Cash Flow Statement Endpoints ---
    "net increase in cash and cash equivalents",
    "net decrease in cash and cash equivalents",
    "net increase / (decrease) in cash and cash equivalents",
    "net change in cash and cash equivalents",
    "net increase (decrease) in cash, cash equivalents and restricted cash",
    "net cash change",
    "ending cash",
    "ending cash and cash equivalents",
    "cash and cash equivalents at end of year",
    "cash and cash equivalents at end of period",
    "cash and cash equivalents at the close of the year",
    "closing cash and cash equivalents",
    
    # --- Statement of Changes in Equity (SOCE) ---
    "ending retained earnings",
    "ending balance",
    "balance at end of year",
    "balance at the end of the reporting period",
    "closing balance"
]

SUBTOTAL_SIGNATURES = [
    # --- Balance Sheet Subtotals ---
    "total current assets",
    "total non-current assets",
    "total noncurrent assets",
    "total tangible assets",
    "total intangible assets",
    "total financial assets",
    "total other assets",
    "total current liabilities",
    "total non-current liabilities",
    "total noncurrent liabilities",
    "total long-term liabilities",
    "total liabilities",
    "total financial liabilities",
    "total provisions",
    "total debt",
    "total borrowings",
    "working capital",
    "net assets",
    
    # --- Income Statement Subtotals ---
    "gross profit",
    "gross profit / (loss)",
    "gross margin",
    "total revenues",
    "total revenue from operations",
    "total cost of sales",
    "total cost of goods sold",
    "total operating expenses",
    "total opex",
    "total overheads",
    "operating income",
    "operating profit",
    "operating income / (loss)",
    "operating profit / (loss)",
    "operating profit before working capital changes",
    "ebitda",
    "adjusted ebitda",
    "ebit",
    "total other income",
    "total other expenses",
    "net finance costs",
    "finance income / (costs)",
    "earnings before taxes",
    "earnings before tax",
    "income before taxes",
    "income before income taxes",
    "profit before tax",
    "profit before taxation",
    "profit before income tax expense",
    "total tax expense",
    "provision for income taxes",
    "income tax provision",
    "income from continuing operations",
    "loss from discontinued operations",
    
    # --- Cash Flow Statement Subtotals ---
    "net cash provided by operating activities",
    "net cash used in operating activities",
    "net cash from operating activities",
    "net cash flow from operating activities",
    "operating cash flow",
    "cash flows from operating activities",
    "cash generated from operations",
    
    "net cash provided by investing activities",
    "net cash used in investing activities",
    "net cash from investing activities",
    "net cash flow from investing activities",
    "investing cash flow",
    "cash flows from investing activities",
    
    "net cash provided by financing activities",
    "net cash used in financing activities",
    "net cash from financing activities",
    "net cash flow from financing activities",
    "financing cash flow",
    "cash flows from financing activities",
    
    # --- Generic Subtotals ---
    "subtotal",
    "sub-total",
    "total"
]

def determine_row_type(
    raw_desc: str,
    cy_val: Optional[Decimal],
    py_val: Optional[Decimal]
) -> str:
    """
    Classifies row as:
      - 'HEADER': Section title without numeric values (e.g., 'ASSETS', 'Current assets:')
      - 'TOTAL': Primary financial statement bottom-line total
      - 'SUBTOTAL': Group roll-up line item
      - 'LINE': Regular operational transaction line
    """

    desc_clean = raw_desc.strip().lower()

    # 1. Total check
    if any(sig == desc_clean or desc_clean.startswith(sig) for sig in TOTAL_SIGNATURES):
        return "TOTAL"

    # 2. Subtotal check
    if any(sig in desc_clean for sig in SUBTOTAL_SIGNATURES):
        return "SUBTOTAL"

    # 3. Header check (has text description but no values)
    if cy_val is not None and py_val is None:
        return "HEADER"

    # 4. Standard operational line item
    return "LINE"