from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.ingestion.excel_loader import load_excel_sources, load_excel_sheet


def test_load_excel_sources_success():
    """Test loading sheets from a mocked Excel workbook without accessing disk."""
    sample_file = Path("fake_report.xlsx")

    # Mock workbook & worksheet setup
    mock_workbook = MagicMock()
    mock_workbook.sheetnames = ["Sheet1"]

    mock_sheet = MagicMock()
    mock_sheet.iter_rows.return_value = [
        ["Name", "Age", "City"],
        ["Alice", 21, "Pune"],
        ["Bob", 22, "Mumbai"],
    ]
    mock_workbook.__getitem__.return_value = mock_sheet

    with patch("src.ingestion.excel_loader.Path.exists", return_value=True), patch(
        "src.ingestion.excel_loader.openpyxl.load_workbook", return_value=mock_workbook
    ) as mock_load:
        sheets = load_excel_sources([sample_file])

    # Validate openpyxl called correctly
    assert mock_load.call_count == 2  # Once for sheetnames, once in load_excel_sheet

    # Validate output structure
    assert len(sheets) == 1
    s = sheets[0]
    assert s.source_filename == "fake_report.xlsx"
    assert s.sheet_name == "Sheet1"
    assert s.row_count == 3
    assert s.col_count == 3
    assert s.raw_grid == [
        ["Name", "Age", "City"],
        ["Alice", 21, "Pune"],
        ["Bob", 22, "Mumbai"],
    ]


def test_load_excel_sources_multiple_sheets():
    """Test loading multiple sheets from a single workbook."""
    sample_file = Path("multi_tab.xlsx")

    mock_workbook = MagicMock()
    mock_workbook.sheetnames = ["Balance Sheet", "Income Statement"]

    mock_bs = MagicMock()
    mock_bs.iter_rows.return_value = [["Assets", 1000], ["Liabilities", 400]]

    mock_is = MagicMock()
    mock_is.iter_rows.return_value = [["Revenue", 5000], ["Net Income", 1200]]

    mock_workbook.__getitem__.side_effect = lambda name: {
        "Balance Sheet": mock_bs,
        "Income Statement": mock_is,
    }[name]

    with patch("src.ingestion.excel_loader.Path.exists", return_value=True), patch(
        "src.ingestion.excel_loader.openpyxl.load_workbook", return_value=mock_workbook
    ):
        sheets = load_excel_sources([sample_file])

    assert len(sheets) == 2
    assert sheets[0].sheet_name == "Balance Sheet"
    assert sheets[0].row_count == 2
    assert sheets[0].raw_grid[0] == ["Assets", 1000]

    assert sheets[1].sheet_name == "Income Statement"
    assert sheets[1].row_count == 2
    assert sheets[1].raw_grid[1] == ["Net Income", 1200]


def test_load_excel_sources_file_not_found():
    """Test FileNotFoundError is raised when target Excel file does not exist."""
    sample_file = Path("non_existent.xlsx")

    with patch("src.ingestion.excel_loader.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Source file not found"):
            load_excel_sources([sample_file])


def test_load_excel_sources_empty_sheet():
    """Test loading an empty worksheet returns 0 rows and 0 cols."""
    sample_file = Path("empty.xlsx")

    mock_workbook = MagicMock()
    mock_workbook.sheetnames = ["EmptySheet"]

    mock_sheet = MagicMock()
    mock_sheet.iter_rows.return_value = []
    mock_workbook.__getitem__.return_value = mock_sheet

    with patch("src.ingestion.excel_loader.Path.exists", return_value=True), patch(
        "src.ingestion.excel_loader.openpyxl.load_workbook", return_value=mock_workbook
    ):
        sheets = load_excel_sources([sample_file])

    assert len(sheets) == 1
    assert sheets[0].row_count == 0
    assert sheets[0].col_count == 0
    assert sheets[0].raw_grid == []


def test_load_excel_sources_ragged_rows():
    """Test col_count calculation when rows have varying numbers of cells."""
    sample_file = Path("ragged.xlsx")

    mock_workbook = MagicMock()
    mock_workbook.sheetnames = ["RaggedSheet"]

    mock_sheet = MagicMock()
    mock_sheet.iter_rows.return_value = [
        ["Title"],
        ["Col1", "Col2", "Col3", "Col4", "Col5"],
        ["Val1", "Val2"],
    ]
    mock_workbook.__getitem__.return_value = mock_sheet

    with patch("src.ingestion.excel_loader.Path.exists", return_value=True), patch(
        "src.ingestion.excel_loader.openpyxl.load_workbook", return_value=mock_workbook
    ):
        sheets = load_excel_sources([sample_file])

    assert sheets[0].row_count == 3
    assert sheets[0].col_count == 5


def test_load_excel_sheet_direct():
    """Direct unit test for load_excel_sheet function."""
    sample_file = Path("direct.xlsx")

    mock_workbook = MagicMock()
    mock_sheet = MagicMock()
    mock_sheet.iter_rows.return_value = [["Header"], ["Data"]]
    mock_workbook.__getitem__.return_value = mock_sheet

    with patch("src.ingestion.excel_loader.openpyxl.load_workbook", return_value=mock_workbook):
        payload = load_excel_sheet(sample_file, "Sheet1")

    assert payload.source_filename == "direct.xlsx"
    assert payload.sheet_name == "Sheet1"
    assert payload.row_count == 2
    assert payload.col_count == 1
    assert payload.raw_grid == [["Header"], ["Data"]]


def test_load_excel_openpyxl_exception():
    """Test that openpyxl exceptions are propagated correctly."""
    sample_file = Path("corrupt.xlsx")

    with patch("src.ingestion.excel_loader.Path.exists", return_value=True), patch(
        "src.ingestion.excel_loader.openpyxl.load_workbook", side_effect=Exception("Corrupt file")
    ):
        with pytest.raises(Exception, match="Corrupt file"):
            load_excel_sources([sample_file])