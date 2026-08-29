import re
from typing import Dict, List, Optional, Tuple


def _extract_year_from_header(cell_text: str) -> Optional[int]:
    """Extracts a 4-digit or 2-digit year number from a header cell string."""
    text = str(cell_text).strip()
    
    # 1. Match full 4-digit years like '2026', 'FY 2025-26', 'FY2026'
    match_4digit = re.search(r"\b20(\d{2})\b", text)
    if match_4digit:
        return int("20" + match_4digit.group(1))

    # 2. Match fiscal spans like '2025-26' or 'FY25-26' -> take ending year (2026)
    match_span = re.search(r"\b(?:FY\s*)?\d{2}[-/](\d{2})\b", text, re.IGNORECASE)
    if match_span:
        return int("20" + match_span.group(1))

    # 3. Match explicit CY / PY tokens
    if re.search(r"\b(current|cy|current year)\b", text, re.IGNORECASE):
        return 9999  # Sentinel for Current Year
    if re.search(r"\b(prior|py|prior year|previous)\b", text, re.IGNORECASE):
        return 1000  # Sentinel for Prior Year

    return None


def detect_table_structure(
    raw_grid: List[List[any]]
) -> Tuple[int, int, Optional[int], Optional[int]]:
    """
    Locates the table header row and resolves column indices:
    Returns:
        header_row_idx: int
        desc_col_idx: int
        cy_col_idx: Optional[int]
        py_col_idx: Optional[int]
    """
    header_row_idx = -1
    desc_col_idx = 0
    cy_col_idx = None
    py_col_idx = None

    # 1. Locate the Header Row (Scan first 10 rows)
    for r_idx, row in enumerate(raw_grid[:10]):
        non_empty = [str(c).strip() for c in row if c is not None and str(c).strip()]
        if not non_empty:
            continue

        # Look for description keywords or multiple year columns
        has_desc = any(re.search(r"\b(line item|particulars|description|account)\b", str(c), re.IGNORECASE) for c in non_empty)
        years_found = [c for c in row if _extract_year_from_header(str(c)) is not None]

        if has_desc or len(years_found) >= 2:
            header_row_idx = r_idx
            break

    # Fallback to row 0 if no explicit header keyword found
    if header_row_idx == -1:
        header_row_idx = 0

    header_row = raw_grid[header_row_idx]

    # 2. Determine Description Column Index
    for c_idx, cell in enumerate(header_row):
        cell_str = str(cell).lower().strip()
        if any(kw in cell_str for kw in ["line item", "particulars", "description", "account"]):
            desc_col_idx = c_idx
            break

    # 3. Disambiguate CY and PY Columns
    detected_years: List[Tuple[int, int]] = []  # (col_idx, year_value)

    for c_idx, cell in enumerate(header_row):
        if c_idx == desc_col_idx or cell is None:
            continue
        year_val = _extract_year_from_header(str(cell))
        if year_val is not None:
            detected_years.append((c_idx, year_val))

    if len(detected_years) >= 2:
        # Sort descending by year value: higher year is CY, lower year is PY
        detected_years.sort(key=lambda x: x[1], reverse=True)
        cy_col_idx = detected_years[0][0]
        py_col_idx = detected_years[1][0]
    elif len(detected_years) == 1:
        cy_col_idx = detected_years[0][0]
    else:
        # Heuristic fallback: assign first numeric column as CY, second as PY
        numeric_candidates = [i for i in range(len(header_row)) if i != desc_col_idx]
        if len(numeric_candidates) >= 2:
            cy_col_idx = numeric_candidates[0]
            py_col_idx = numeric_candidates[1]
        elif len(numeric_candidates) == 1:
            cy_col_idx = numeric_candidates[0]

    return header_row_idx, desc_col_idx, cy_col_idx, py_col_idx