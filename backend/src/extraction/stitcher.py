import re
from typing import Dict, List
from backend.src.schemas.manifest import RawSheetPayload, StatementType

def is_likely_header_row(row: List[any]) -> bool:
    """Detects if a row is a table column header"""
    non_empty = [str(c).strip().lower() for c in row if c is not None and str(c).strip()]
    if not non_empty:
        return False

    header_signals = ["line item", "particulars", "description", "note", "inr", "usd", "eur", "fy", "cy", "py", "202"]
    matches = sum(1 for s in header_signals if any(s in cell for cell in non_empty))
    return matches >= 2

def stitch_statement_pages(sheets: List[RawSheetPayload]) -> Dict[StatementType, List[List[any]]]:
    """Groups sheets/pages by StatementType, merges multi-page tables,
    and drops deduplicated header rows appearing after page breaks."""

    grouped_grids: Dict[StatementType, List[List[any]]] = {}


    for s in sheets:
        if s.detected_type == StatementType.UNKNOWN:
            continue

        if s.detected_type not in grouped_grids:
            grouped_grids[s.detected_type] = list(s.raw_grid)
        else:
            # Subsequent page for the same statement: Stitch and deduplicate top headers
            existing_grid = grouped_grids[s.detected_type]
            page_rows = s.raw_grid

            start_idx = 0
            # Scan top 5 rows of subsequent page to skip repeated header rows
            for idx, r in enumerate(page_rows[:5]):
                if is_likely_header_row(r):
                    start_idx = idx + 1

            existing_grid.extend(page_rows[start_idx:])

    return grouped_grids