from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.src.ingestion.classifier import classify_sheet, extract_metadata, extract_metadata_from_grid
from backend.src.ingestion.excel_loader import load_excel_sources
from backend.src.schemas.manifest import RawSheetPayload, StatementType


@pytest.mark.parametrize(
    "sheet_name,expected_type",
    [
        ("Balance Sheet", StatementType.BALANCE_SHEET),
        ("Consolidated Statement of Financial Position", StatementType.BALANCE_SHEET),
        ("Profit and Loss", StatementType.INCOME_STATEMENT),
        ("Statement of Operations", StatementType.INCOME_STATEMENT),
        ("Cash Flow Statement", StatementType.CASH_FLOW_STATEMENT),
        ("Statement of Changes in Equity", StatementType.SOCE),
        ("Trial Balance", StatementType.TRIAL_BALANCE),
        ("Accounts Receivable Aging", StatementType.AR_AGING),
        ("PPE Schedule", StatementType.PPE_SCHEDULE),
        ("Debt Maturity Schedule", StatementType.DEBT_MATURITY),
    ],
)
def test_classify_sheet_by_name(sheet_name, expected_type):
    """Test sheet classification based on sheet tab name keywords."""
    payload = RawSheetPayload(
        source_filename="test.xlsx",
        sheet_name=sheet_name,
        raw_grid=[],
        detected_type=StatementType.UNKNOWN,
    )
    assert classify_sheet(payload) == expected_type


def test_classify_sheet_by_content_signatures():
    """Test sheet classification using content signatures when tab name is generic."""
    payload = RawSheetPayload(
        source_filename="report.xlsx",
        sheet_name="Tab 1",
        raw_grid=[
            ["Line Item", "2023"],
            ["Total Assets", "1,000,000"],
            ["Stockholders' Equity", "500,000"],
        ],
        raw_text="",
        detected_type=StatementType.UNKNOWN,
    )
    assert classify_sheet(payload) == StatementType.BALANCE_SHEET


def test_classify_sheet_preserves_existing_type():
    """Test that classify_sheet preserves detected_type if already set (e.g. from PDF TOC)."""
    payload = RawSheetPayload(
        source_filename="report.pdf",
        sheet_name="Page 1",
        raw_grid=[["Random Text"]],
        detected_type=StatementType.CASH_FLOW_STATEMENT,
    )
    assert classify_sheet(payload) == StatementType.CASH_FLOW_STATEMENT


def test_classify_sheet_unknown():
    """Test sheet classification returns UNKNOWN for unrecognized content."""
    payload = RawSheetPayload(
        source_filename="test.xlsx",
        sheet_name="Custom Notes",
        raw_grid=[["Random text without financial signatures"]],
        raw_text="",
        detected_type=StatementType.UNKNOWN,
    )
    assert classify_sheet(payload) == StatementType.UNKNOWN


def test_extract_metadata_full():
    """Test metadata extraction for client name, currency, scale, and period ended."""
    raw_text = """
    ACME International Corp.
    Consolidated Balance Sheet
    Amounts in Millions USD
    For the period ended December 31, 2023
    """
    payload = RawSheetPayload(
        source_filename="report.pdf",
        sheet_name="Page 1",
        raw_grid=[],
        raw_text=raw_text,
    )

    meta = extract_metadata(payload)
    assert meta.client_name == "ACME International Corp."
    assert meta.currency == "USD"
    assert meta.scale == "MILLIONS"
    assert meta.period_ended == "December 31, 2023"


def test_extract_metadata_from_grid_alias():
    """Test metadata extraction from a 2D raw grid list via backward-compatible alias."""
    grid = [
        ["Global Tech Ltd."],
        ["Balance Sheet"],
        ["In Thousands INR"],
        ["As of 2023-12-31"],
    ]

    meta = extract_metadata_from_grid(grid)
    assert meta.client_name == "Global Tech Ltd."
    assert meta.currency == "INR"
    assert meta.scale == "THOUSANDS"
    assert meta.period_ended == "2023-12-31"


def test_sheet_classification_integration_mocked():
    """Unit test for loading and classifying sheets using a mocked Excel workbook."""
    sample_file = Path("Book1.xlsx")

    mock_workbook = MagicMock()
    mock_workbook.sheetnames = ["Balance Sheet", "P&L"]

    mock_bs = MagicMock()
    mock_bs.iter_rows.return_value = [
        ["ACME Enterprises Inc."],
        ["Balance Sheet"],
        ["Total Assets", 5000],
    ]

    mock_pnl = MagicMock()
    mock_pnl.iter_rows.return_value = [
        ["ACME Enterprises Inc."],
        ["Profit & Loss"],
        ["Revenue", 10000],
    ]

    mock_workbook.__getitem__.side_effect = lambda name: {
        "Balance Sheet": mock_bs,
        "P&L": mock_pnl,
    }[name]

    with patch("src.ingestion.excel_loader.Path.exists", return_value=True), patch(
        "src.ingestion.excel_loader.openpyxl.load_workbook", return_value=mock_workbook
    ):
        sheets = load_excel_sources([sample_file])

    assert len(sheets) == 2

    # Verify metadata and classification
    meta = extract_metadata_from_grid(sheets[0].raw_grid)
    assert meta.client_name == "ACME Enterprises Inc."

    sheets[0].detected_type = classify_sheet(sheets[0])
    sheets[1].detected_type = classify_sheet(sheets[1])

    assert sheets[0].detected_type == StatementType.BALANCE_SHEET
    assert sheets[1].detected_type == StatementType.INCOME_STATEMENT