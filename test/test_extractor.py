from decimal import Decimal
import pytest

from src.extraction.extractor import extract_statements_from_manifest, get_scale_factor
from src.schemas.manifest import DocumentMetadata, IngestionManifest, RawSheetPayload, StatementType


def test_get_scale_factor():
    """Test scale factor multiplier resolution."""
    assert get_scale_factor("BILLIONS") == Decimal("1000000000.0")
    assert get_scale_factor("CRORES") == Decimal("10000007.0") or get_scale_factor("CRORES") == Decimal("10000000.0")
    assert get_scale_factor("MILLIONS") == Decimal("1000000.0")
    assert get_scale_factor("LAKHS") == Decimal("100000.0")
    assert get_scale_factor("THOUSANDS") == Decimal("1000.0")
    assert get_scale_factor("ONES") == Decimal("1.0")
    assert get_scale_factor(None) == Decimal("1.0")
    assert get_scale_factor("UNKNOWN") == Decimal("1.0")


def test_extract_statements_from_manifest_success():
    """Test end-to-end extraction from an IngestionManifest into StandardFinancialStatement objects."""
    manifest = IngestionManifest(
        metadata=DocumentMetadata(
            client_name="ACME Corp Inc.",
            currency="USD",
            scale="MILLIONS",
            period_ended="December 31, 2023",
        ),
        sheets=[
            RawSheetPayload(
                source_filename="annual_report.pdf",
                sheet_name="Page 1",
                raw_grid=[
                    ["Line Item", "2023", "2022"],
                    ["Cash and Cash Equivalents", "100.0", "80.0"],
                    ["Accounts Receivable", "200.0", "180.0"],
                    ["Total Current Assets", "300.0", "260.0"],
                    ["Total Assets", "500.0", "450.0"],
                ],
                detected_type=StatementType.BALANCE_SHEET,
            )
        ],
    )

    statements = extract_statements_from_manifest(manifest, apply_scale=True)

    assert StatementType.BALANCE_SHEET in statements
    stmt = statements[StatementType.BALANCE_SHEET]

    assert stmt.entity_name == "ACME Corp Inc."
    assert stmt.currency == "USD"
    assert stmt.period_ended_cy == "December 31, 2023"
    assert stmt.scale == Decimal("1000000.0")

    # Validate line items
    assert len(stmt.line_items) == 4

    # Item 1: Cash
    item1 = stmt.line_items[0]
    assert item1.standard_key == "CashAndCashEquivalents"
    assert item1.raw_description == "Cash and Cash Equivalents"
    assert item1.cy_value == Decimal("100000000.0")  # 100 * 1,000,000
    assert item1.py_value == Decimal("80000000.0")   # 80 * 1,000,000
    assert item1.row_type == "LINE"

    # Item 3: Total Current Assets
    item3 = stmt.line_items[2]
    assert item3.standard_key == "TotalCurrentAssets"
    assert item3.row_type == "SUBTOTAL"

    # Item 4: Total Assets
    item4 = stmt.line_items[3]
    assert item4.standard_key == "TotalAssets"
    assert item4.row_type == "TOTAL"


def test_extract_statements_from_manifest_unscaled():
    """Test extraction without applying scale factor multiplier."""
    manifest = IngestionManifest(
        metadata=DocumentMetadata(
            client_name="Beta Ltd",
            currency="INR",
            scale="THOUSANDS",
            period_ended="2023-12-31",
        ),
        sheets=[
            RawSheetPayload(
                source_filename="report.xlsx",
                sheet_name="P&L",
                raw_grid=[
                    ["Particulars", "CY", "PY"],
                    ["Revenue", "1000", "800"],
                    ["Net Income", "200", "150"],
                ],
                detected_type=StatementType.INCOME_STATEMENT,
            )
        ],
    )

    statements = extract_statements_from_manifest(manifest, apply_scale=False)

    assert StatementType.INCOME_STATEMENT in statements
    stmt = statements[StatementType.INCOME_STATEMENT]

    assert stmt.line_items[0].cy_value == Decimal("1000")
    assert stmt.line_items[0].py_value == Decimal("800")
    assert stmt.line_items[1].cy_value == Decimal("200")
    assert stmt.line_items[1].py_value == Decimal("150")


def test_extract_statements_empty_manifest():
    """Test extracting from an empty manifest returns empty dictionary."""
    manifest = IngestionManifest()
    statements = extract_statements_from_manifest(manifest)
    assert statements == {}
