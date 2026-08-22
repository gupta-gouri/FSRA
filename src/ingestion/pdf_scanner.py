import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
import pymupdf
from src.schemas.manifest import StatementType

STATEMENT_TOC_PATTERNS = {
    StatementType.BALANCE_SHEET: r"(?:balance\s+sheet|statement\s+of\s+financial\s+position)",
    StatementType.INCOME_STATEMENT: r"(?:income\s+statement|statement\s+of\s+operations|statement\s+of\s+profit\s+and\s+loss|profit\s*&\s*loss)",
    StatementType.CASH_FLOW_STATEMENT: r"(?:cash\s+flow\s+statement|statement\s+of\s+cash\s+flows)",
    StatementType.SOCE: r"(?:statement\s+of\s+stockholders['’]?\s+equity|statement\s+of\s+changes\s+in\s+equity|statement\s+of\s+equity)",
    StatementType.AR_AGING: r"(?:accounts?\s+receivable\s+aging|trade\s+receivables\s+aging)",
    StatementType.DEBT_MATURITY: r"(?:maturities\s+of\s+debt|debt\s+schedule|borrowings\s+schedule)"
}

def extract_pages_from_digital_toc(doc: pymupdf.Document) -> Dict[StatementType, int]:
    """Extract target page numbers from PDF"""
    toc = doc.get_toc() # Return list of [lvl, title, page no]
    target_pages: Dict[StatementType, int] = {}

    for item in toc:
        if len(item) >= 3:
            title = str(item[1]).lower()
            page_no = int(item[2])
            for stmt_type, pattern in STATEMENT_TOC_PATTERNS.items():
                if stmt_type not in target_pages and re.search(pattern, title):
                    target_pages[stmt_type] = page_no

    return target_pages

def extract_pages_from_printed_toc(doc: pymupdf.Document, max_toc_pages: int = 10) -> Dict[StatementType, int]:
    """Scans the first 10 pages for printed TOC entries matching statement titles and page no"""
    target_pages: Dict[StatementType, int] = {}

    # Check only early pages where TOC typically lives
    pages_to_check = min(max_toc_pages, len(doc))

    for page_idx in range(pages_to_check):
        text = doc[page_idx].get_text()
        text_lower = text.lower()

        # Check if page is indeed a TOC
        if "table of contents" in text_lower or "contents" in text_lower or "index" in text_lower:
            for line in text.split("\n"):
                line_lower = line.lower()

                for stmt_type, pattern in STATEMENT_TOC_PATTERNS.items():
                    if stmt_type not in target_pages and re.search(pattern, line_lower):
                        # Find trailing page no in TOC
                        num_match = re.search(r"(\d{1,4})\s*$", line.strip())
                        if num_match:
                            target_pages[stmt_type] = int(num_match.group(1))

    return target_pages

def full_scan_page_discovery(doc: pymupdf.Document) -> Dict[StatementType, int]:
    """Fallback: Performs a fast text scan across all pages to locate primary statements."""
    target_pages: Dict[StatementType, int] = {}

    for page_idx, page in enumerate(doc, start=1):
        # Read the top 500 characters of each page (where statement headers appear)
        header_text = page.get_text()[:500].lower()

        for stmt_type, pattern in STATEMENT_TOC_PATTERNS.items():
            if stmt_type not in target_pages:
                if re.search(pattern, header_text):
                    target_pages[stmt_type] = page_idx

    return target_pages

def discover_statement_pages(file_path: Union[str, Path]) -> Dict[StatementType, int]:
    """Orchestrates PDF page discovery: Digital TOC -> Printed TOC -> Full Document Scan."""
    doc = pymupdf.open(file_path)

    # 1. Try Digital Bookmarks
    pages = extract_pages_from_digital_toc(doc)

    # 2. Try Printed TOC scan if bookmarks are empty or incomplete
    if len(pages) < 3:
        printed_pages = extract_pages_from_printed_toc(doc)
        for k, v in printed_pages.items():
            if k not in pages:
                pages[k] = v

    # 3. Fallback: Full scan across document pages if TOC yields incomplete results
    if len(pages) < 3:
        full_pages = full_scan_page_discovery(doc)
        for k, v in full_pages.items():
            if k not in pages:
                pages[k] = v

    doc.close()
    return pages

