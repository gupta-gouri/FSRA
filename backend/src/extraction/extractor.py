from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from backend.src.schemas.manifest import IngestionManifest, StatementType
from backend.src.schemas.statements import StandardFinancialStatement, StandardLineItem, StandardTrialBalance
from backend.src.extraction.stitcher import stitch_statement_pages
from backend.src.extraction.column_extractor import detect_table_structure
from backend.src.extraction.numeric_parser import parse_financial_number
from backend.src.extraction.row_tagger import determine_row_type
from backend.src.extraction.taxonomy import normalize_line_item_key
from backend.src.extraction.tb_extractor import extract_trial_balance

SCALE_MULTIPLIERS: Dict[str, Decimal] = {
    "BILLIONS": Decimal("1000000000.0"),
    "CRORES": Decimal("10000000.0"),
    "MILLIONS": Decimal("1000000.0"),
    "LAKHS": Decimal("100000.0"),
    "THOUSANDS": Decimal("1000.0"),
    "ONES": Decimal("1.0")
}


def get_scale_factor(scale_str: Optional[str]) -> Decimal:
    if not scale_str:
        return Decimal("1.0")
    return SCALE_MULTIPLIERS.get(scale_str.upper().strip(), Decimal("1.0"))


def extract_statements_from_manifest(
    manifest: IngestionManifest,
    apply_scale: bool = False
) -> Dict[str, Any]:
    """
    Stage 2 Entry Point:
    Extracts StandardFinancialStatement objects for primary statements
    and StandardTrialBalance with Lead Sheet groupings if TB is present.
    """
    scale_factor = get_scale_factor(manifest.metadata.scale) if apply_scale else Decimal("1.0")
    currency = manifest.metadata.currency or "USD"
    client_name = manifest.metadata.client_name or "Unknown Entity"
    period_ended = manifest.metadata.period_ended or "CY"

    extracted_data: Dict[str, Any] = {}

    # 1. Check for Trial Balance in IngestionManifest
    for sheet in manifest.sheets:
        if sheet.detected_type == StatementType.TRIAL_BALANCE:
            tb_model = extract_trial_balance(sheet, client_name=client_name, period_ended=period_ended)
            extracted_data["TRIAL_BALANCE"] = tb_model
            break

    # 2. Stitch and process primary financial statements
    stitched_grids = stitch_statement_pages(manifest.sheets)

    for stmt_type, grid in stitched_grids.items():
        if stmt_type == StatementType.TRIAL_BALANCE or not grid or len(grid) < 2:
            continue

        hdr_idx, desc_col, cy_col, py_col = detect_table_structure(grid)
        line_items: List[StandardLineItem] = []

        for row_idx, row in enumerate(grid[hdr_idx + 1:], start=hdr_idx + 1):
            if not row or desc_col >= len(row) or row[desc_col] is None:
                continue

            raw_desc = str(row[desc_col]).strip()
            if not raw_desc:
                continue

            cy_raw = row[cy_col] if (cy_col is not None and cy_col < len(row)) else None
            cy_dec = parse_financial_number(cy_raw)
            if cy_dec is not None and apply_scale:
                cy_dec = cy_dec * scale_factor

            py_raw = row[py_col] if (py_col is not None and py_col < len(row)) else None
            py_dec = parse_financial_number(py_raw)
            if py_dec is not None and apply_scale:
                py_dec = py_dec * scale_factor

            row_type = determine_row_type(raw_desc, cy_dec, py_dec)
            standard_key = normalize_line_item_key(raw_desc)

            line_items.append(
                StandardLineItem(
                    standard_key=standard_key,
                    raw_description=raw_desc,
                    cy_value=cy_dec,
                    py_value=py_dec,
                    row_type=row_type,
                    row_index=row_idx
                )
            )

        extracted_data[stmt_type.value] = StandardFinancialStatement(
            statement_type=stmt_type,
            entity_name=client_name,
            period_ended_cy=period_ended,
            currency=currency,
            scale=scale_factor,
            line_items=line_items
        )

    return extracted_data