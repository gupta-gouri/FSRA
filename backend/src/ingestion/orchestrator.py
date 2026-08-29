from pathlib import Path
from typing import List, Union

from backend.src.schemas.manifest import (
    DocumentMetadata,
    IngestionManifest,
    RawSheetPayload,
    StatementType,
)
from backend.src.ingestion.classifier import classify_sheet, extract_metadata
from backend.src.ingestion.excel_loader import load_excel_sources
from backend.src.ingestion.pdf_loader import load_pdf_pages
from backend.src.ingestion.resolver import resolve_statement_conflicts, REQUIRED_STATEMENTS

def ingest_sources(
    file_paths: List[Union[str, Path]],
    resolve_conflicts: bool = False,
    interactive: bool = False
) -> IngestionManifest:
    """Unified Stage 1 Entry point:
    Accepts any combination of Excel workbooks (.xlsx, .xls, .xlsm) and PDF reports (.pdf) ,
    extracts pages/sheets into uniform grids and raw text, 
    classifies financial statements,
    optionally resolves statement conflicts via human-in-the-loop verification,
    and aggregates global client metadata."""

    raw_payloads: List[RawSheetPayload] = []

    # 1. Ingest files dynamically based on extension
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")

        ext = path.suffix.lower()

        if ext in [".xlsx", ".xls", ".xlsm"]:
            raw_payloads.extend(load_excel_sources([path]))
        elif ext == ".pdf":
            raw_payloads.extend(load_pdf_pages(path))
        else:
            raise ValueError(f"Unsupported file format: {path.name}. Only .xlsx, .xls, .xlsm, and .pdf are supported.")

    master_metadata = DocumentMetadata()
    classified_payloads: List[RawSheetPayload] = []

    # 2. Classify each sheet.page
    for item in raw_payloads:
        item.detected_type = classify_sheet(item)
        classified_payloads.append(item)

    # 3. Human in the loop verification & conflict resolution (optional)
    if resolve_conflicts or interactive:
        classified_payloads = resolve_statement_conflicts(
            sheets=classified_payloads,
            required_types=REQUIRED_STATEMENTS,
            interactive=interactive
        )
    # 4. Extract and consolidate metadata (prioritize core statements)
    priority_order = [
        StatementType.BALANCE_SHEET,
        StatementType.INCOME_STATEMENT,
        StatementType.CASH_FLOW_STATEMENT,
        StatementType.SOCE,
    ]

    sorted_payloads = sorted(
        classified_payloads,
        key=lambda s:priority_order.index(s.detected_type)
    if s.detected_type in priority_order 
    else 99,
    )

    for item in sorted_payloads:
        item_meta = extract_metadata(item)

        if not master_metadata.client_name and item_meta.client_name:
            master_metadata.client_name = item_meta.client_name
        if not master_metadata.period_ended and item_meta.period_ended:
            master_metadata.period_ended = item_meta.period_ended
        if not master_metadata.currency and item_meta.currency:
            master_metadata.currency = item_meta.currency
        if not master_metadata.scale and item_meta.scale:
            master_metadata.scale = item_meta.scale

    return IngestionManifest(
        metadata=master_metadata,
        sheets=classified_payloads,
    )