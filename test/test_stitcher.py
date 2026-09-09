from src.extraction.stitcher import is_likely_header_row, stitch_statement_pages
from src.schemas.manifest import RawSheetPayload, StatementType


def test_is_likely_header_row():
    """Test detecting table header rows."""
    assert is_likely_header_row(["Line Item", "Notes", "CY 2023", "PY 2022"]) is True
    assert is_likely_header_row(["Particulars", "FY 2023", "FY 2022"]) is True
    assert is_likely_header_row(["Cash and cash equivalents", "100", "80"]) is False
    assert is_likely_header_row([]) is False


def test_stitch_statement_pages_single_sheet():
    """Test stitching a single page sheet."""
    sheets = [
        RawSheetPayload(
            source_filename="report.pdf",
            sheet_name="Page 1",
            raw_grid=[["Particulars", "CY"], ["Cash", "100"]],
            detected_type=StatementType.BALANCE_SHEET,
        )
    ]
    stitched = stitch_statement_pages(sheets)

    assert StatementType.BALANCE_SHEET in stitched
    assert len(stitched[StatementType.BALANCE_SHEET]) == 2
    assert stitched[StatementType.BALANCE_SHEET] == [["Particulars", "CY"], ["Cash", "100"]]


def test_stitch_statement_pages_multi_page():
    """Test stitching multi-page statement and deduplicating top header rows."""
    sheets = [
        RawSheetPayload(
            source_filename="report.pdf",
            sheet_name="Page 1",
            raw_grid=[["Line Item", "2023"], ["Assets", "1000"]],
            detected_type=StatementType.BALANCE_SHEET,
        ),
        RawSheetPayload(
            source_filename="report.pdf",
            sheet_name="Page 2",
            raw_grid=[["Line Item", "2023"], ["Liabilities", "400"], ["Equity", "600"]],
            detected_type=StatementType.BALANCE_SHEET,
        ),
    ]
    stitched = stitch_statement_pages(sheets)

    grid = stitched[StatementType.BALANCE_SHEET]
    assert len(grid) == 4
    # Header on Page 2 ("Line Item", "2023") should be stripped
    assert grid == [["Line Item", "2023"], ["Assets", "1000"], ["Liabilities", "400"], ["Equity", "600"]]


def test_stitch_statement_pages_ignores_unknown():
    """Test that UNKNOWN statement sheets are ignored during stitching."""
    sheets = [
        RawSheetPayload(
            source_filename="report.pdf",
            sheet_name="Page 1",
            raw_grid=[["Random Notes"]],
            detected_type=StatementType.UNKNOWN,
        )
    ]
    stitched = stitch_statement_pages(sheets)
    assert len(stitched) == 0
