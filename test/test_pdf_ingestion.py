from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.src.ingestion.orchestrator import ingest_sources
from backend.src.ingestion.pdf_loader import load_pdf_pages
from backend.src.ingestion.pdf_scanner import discover_statement_pages
from backend.src.schemas.manifest import StatementType


def test_pdf_discovery_and_scanning_mocked():
    """Unit test for PDF discovery and full ingestion pipeline using PyMuPDF and pdfplumber mocks."""
    pdf_file = Path("sample_annual_report.pdf")

    # 1. Mock PyMuPDF doc for discover_statement_pages
    mock_pymupdf_doc = MagicMock()
    mock_pymupdf_doc.get_toc.return_value = []
    mock_pymupdf_doc.__len__.return_value = 3

    # Setup 3 pages for full scan discovery
    mock_pymupdf_page1 = MagicMock()
    mock_pymupdf_page1.get_text.return_value = "ACME Corp Inc.\nConsolidated Balance Sheet\nAmounts in Millions USD\nFor period ended December 31, 2023"

    mock_pymupdf_page2 = MagicMock()
    mock_pymupdf_page2.get_text.return_value = "ACME Corp Inc.\nStatement of Operations\nAmounts in Millions USD"

    mock_pymupdf_page3 = MagicMock()
    mock_pymupdf_page3.get_text.return_value = "ACME Corp Inc.\nStatement of Cash Flows\nAmounts in Millions USD"

    mock_pymupdf_doc.__getitem__.side_effect = lambda idx: [
        mock_pymupdf_page1,
        mock_pymupdf_page2,
        mock_pymupdf_page3,
    ][idx]
    mock_pymupdf_doc.__iter__.side_effect = lambda: iter(
        [mock_pymupdf_page1, mock_pymupdf_page2, mock_pymupdf_page3]
    )

    # 2. Mock pdfplumber for load_pdf_pages
    mock_pdfplumber_pdf = MagicMock()
    mock_pdfplumber_pdf.__enter__.return_value = mock_pdfplumber_pdf

    mock_plumber_page1 = MagicMock()
    mock_plumber_page1.extract_text.return_value = (
        "ACME Corp Inc.\nConsolidated Balance Sheet\nAmounts in Millions USD\nFor period ended December 31, 2023"
    )
    mock_plumber_page1.extract_tables.return_value = [
        [["Line Item", "2023", "2022"], ["Cash & Cash Equivalents", "100", "80"], ["Total Assets", "500", "450"]]
    ]

    mock_plumber_page2 = MagicMock()
    mock_plumber_page2.extract_text.return_value = (
        "ACME Corp Inc.\nStatement of Operations\nAmounts in Millions USD\nFor period ended December 31, 2023"
    )
    mock_plumber_page2.extract_tables.return_value = [
        [["Line Item", "2023"], ["Revenues", "1000"], ["Operating Income", "300"]]
    ]

    mock_plumber_page3 = MagicMock()
    mock_plumber_page3.extract_text.return_value = (
        "ACME Corp Inc.\nStatement of Cash Flows\nAmounts in Millions USD\nFor period ended December 31, 2023"
    )
    mock_plumber_page3.extract_tables.return_value = [
        [["Line Item", "2023"], ["Operating Cash Flow", "250"], ["Capital Expenditures", "-50"]]
    ]

    mock_pdfplumber_pdf.pages = [mock_plumber_page1, mock_plumber_page2, mock_plumber_page3]

    with patch("src.ingestion.pdf_scanner.Path.exists", return_value=True), patch(
        "src.ingestion.pdf_loader.Path.exists", return_value=True
    ), patch("src.ingestion.orchestrator.Path.exists", return_value=True), patch(
        "src.ingestion.pdf_scanner.pymupdf.open", return_value=mock_pymupdf_doc
    ), patch(
        "src.ingestion.pdf_loader.pdfplumber.open", return_value=mock_pdfplumber_pdf
    ):
        # 1. Discover statement pages
        discovered = discover_statement_pages(pdf_file)
        assert isinstance(discovered, dict)
        assert len(discovered) == 3
        assert discovered[StatementType.BALANCE_SHEET] == 1
        assert discovered[StatementType.INCOME_STATEMENT] == 2
        assert discovered[StatementType.CASH_FLOW_STATEMENT] == 3

        # 2. Ingest via full pipeline
        manifest = ingest_sources([pdf_file])

    # Validate metadata
    assert manifest.metadata is not None
    assert manifest.metadata.client_name == "ACME Corp Inc."
    assert manifest.metadata.currency == "USD"
    assert manifest.metadata.scale == "MILLIONS"
    assert manifest.metadata.period_ended == "December 31, 2023"

    # Validate extracted statement grids
    assert isinstance(manifest.sheets, list)
    assert len(manifest.sheets) == 3

    sheet_types = [s.detected_type for s in manifest.sheets]
    assert StatementType.BALANCE_SHEET in sheet_types
    assert StatementType.INCOME_STATEMENT in sheet_types
    assert StatementType.CASH_FLOW_STATEMENT in sheet_types

    for s in manifest.sheets:
        assert hasattr(s, "detected_type")
        assert hasattr(s, "sheet_name")
        assert s.row_count > 0
        assert s.col_count > 0
        assert isinstance(s.raw_grid, list)


def test_pdf_discovery_digital_toc_mocked():
    """Test PDF page discovery via digital TOC (bookmarks)."""
    mock_doc = MagicMock()
    mock_doc.get_toc.return_value = [
        [1, "Balance Sheet", 5],
        [1, "Statement of Operations", 10],
        [1, "Statement of Cash Flows", 15],
    ]
    mock_doc.__len__.return_value = 20

    with patch("src.ingestion.pdf_scanner.pymupdf.open", return_value=mock_doc):
        discovered = discover_statement_pages("bookmarks.pdf")

    assert discovered[StatementType.BALANCE_SHEET] == 5
    assert discovered[StatementType.INCOME_STATEMENT] == 10
    assert discovered[StatementType.CASH_FLOW_STATEMENT] == 15


def test_pdf_discovery_printed_toc_mocked():
    """Test PDF page discovery via printed TOC scan."""
    mock_doc = MagicMock()
    mock_doc.get_toc.return_value = []
    mock_doc.__len__.return_value = 10

    toc_page = MagicMock()
    toc_page.get_text.return_value = (
        "Table of Contents\n"
        "Balance Sheet .... 3\n"
        "Income Statement .... 6\n"
        "Cash Flow Statement .... 8\n"
    )
    other_page = MagicMock()
    other_page.get_text.return_value = "Some random text"

    mock_doc.__getitem__.side_effect = lambda idx: toc_page if idx == 0 else other_page

    with patch("src.ingestion.pdf_scanner.pymupdf.open", return_value=mock_doc):
        discovered = discover_statement_pages("printed_toc.pdf")

    assert discovered[StatementType.BALANCE_SHEET] == 3
    assert discovered[StatementType.INCOME_STATEMENT] == 6
    assert discovered[StatementType.CASH_FLOW_STATEMENT] == 8


def test_pdf_loader_file_not_found():
    """Test FileNotFoundError is raised when PDF source file is missing."""
    with patch("src.ingestion.pdf_loader.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="PDF source file not found"):
            load_pdf_pages("non_existent.pdf")


def test_pdf_loader_text_fallback():
    """Test fallback to text line extraction when pdfplumber extract_tables returns empty list."""
    mock_pdfplumber_pdf = MagicMock()
    mock_pdfplumber_pdf.__enter__.return_value = mock_pdfplumber_pdf

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Header Line\nFirst Data Row\nSecond Data Row"
    mock_page.extract_tables.return_value = []  # Empty tables triggers text line fallback
    mock_pdfplumber_pdf.pages = [mock_page]

    with patch("src.ingestion.pdf_loader.Path.exists", return_value=True), patch(
        "src.ingestion.pdf_loader.discover_statement_pages", return_value={}
    ), patch("src.ingestion.pdf_loader.pdfplumber.open", return_value=mock_pdfplumber_pdf):
        payloads = load_pdf_pages("text_only.pdf")

    assert len(payloads) == 1
    p = payloads[0]
    assert p.row_count == 3
    assert p.col_count == 1
    assert p.raw_grid == [["Header Line"], ["First Data Row"], ["Second Data Row"]]


def test_ingest_sources_unsupported_format():
    """Test that ingest_sources raises ValueError for unsupported file formats."""
    with patch("src.ingestion.orchestrator.Path.exists", return_value=True):
        with pytest.raises(ValueError, match="Unsupported file format"):
            ingest_sources(["document.docx"])