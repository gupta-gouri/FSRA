import pytest
from backend.src.extraction.column_extractor import _extract_year_from_header, detect_table_structure


def test_extract_year_from_header_4digit():
    """Test extracting 4-digit years from header cell text."""
    assert _extract_year_from_header("2026") == 2026
    assert _extract_year_from_header("FY 2025") == 2025
    assert _extract_year_from_header("As of Dec 31, 2023") == 2023


def test_extract_year_from_header_span():
    """Test extracting year from fiscal span headers."""
    assert _extract_year_from_header("FY25-26") == 2026
    assert _extract_year_from_header("FY24-25") == 2025


def test_extract_year_from_header_cy_py_tokens():
    """Test CY and PY sentinel value extraction."""
    assert _extract_year_from_header("Current Year") == 9999
    assert _extract_year_from_header("CY") == 9999
    assert _extract_year_from_header("Prior Year") == 1000
    assert _extract_year_from_header("PY") == 1000


def test_extract_year_from_header_invalid():
    """Test returning None for non-year header text."""
    assert _extract_year_from_header("Particulars") is None
    assert _extract_year_from_header("Notes") is None


def test_detect_table_structure_standard_years():
    """Test detecting table headers, description column, CY and PY columns with explicit years."""
    raw_grid = [
        ["Company Financials"],
        ["Line Item", "Notes", "2023", "2022"],
        ["Revenue", "1", "1000", "800"],
        ["Net Income", "2", "300", "200"],
    ]
    hdr_idx, desc_col, cy_col, py_col = detect_table_structure(raw_grid)

    assert hdr_idx == 1
    assert desc_col == 0
    assert cy_col == 2
    assert py_col == 3


def test_detect_table_structure_cy_py_labels():
    """Test detecting table structure using CY / PY label headers."""
    raw_grid = [
        ["Particulars", "CY", "PY"],
        ["Cash", "500", "400"],
    ]
    hdr_idx, desc_col, cy_col, py_col = detect_table_structure(raw_grid)

    assert hdr_idx == 0
    assert desc_col == 0
    assert cy_col == 1
    assert py_col == 2


def test_detect_table_structure_fallback():
    """Test fallback heuristic when no explicit year headers exist."""
    raw_grid = [
        ["Description", "Amount 1", "Amount 2"],
        ["Sales", "100", "90"],
    ]
    hdr_idx, desc_col, cy_col, py_col = detect_table_structure(raw_grid)

    assert hdr_idx == 0
    assert desc_col == 0
    assert cy_col == 1
    assert py_col == 2
