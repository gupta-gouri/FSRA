from pathlib import Path
from typing import List, Union
import pdfplumber

from backend.src.schemas.manifest import RawSheetPayload, StatementType
from backend.src.ingestion.pdf_scanner import discover_statement_pages


def load_pdf_pages(file_path: Union[str, Path]) -> List[RawSheetPayload]:
    """
    Discovers target financial statement pages using TOC & PyMuPDF scanning,
    then extracts both raw text (for metadata/classification) and vector table grids.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF source file not found: {path}")

    # 1. Discover target statement pages
    discovered_pages = discover_statement_pages(path)
    target_page_set = set(discovered_pages.values())
    page_to_type = {v: k for k, v in discovered_pages.items()}

    pdf_payloads: List[RawSheetPayload] = []

    with pdfplumber.open(path) as pdf:
        total_pages = len(pdf.pages)
        pages_to_extract = [
            (idx, pdf.pages[idx - 1]) 
            for idx in sorted(target_page_set) 
            if 1 <= idx <= total_pages
        ] if target_page_set else list(enumerate(pdf.pages, start=1))

        for page_idx, page in pages_to_extract:
            raw_grid: List[List] = []
            page_text = page.extract_text() or ""

            # Extract table cells
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if row and any(cell is not None and str(cell).strip() for cell in row):
                            raw_grid.append([c if c is not None else "" for c in row])
            else:
                # Text line fallback if table extraction is empty
                if page_text:
                    for line in page_text.split("\n"):
                        stripped = line.strip()
                        if stripped:
                            raw_grid.append([stripped])

            # Use discovered TOC type or default to UNKNOWN
            assigned_type = page_to_type.get(page_idx, StatementType.UNKNOWN)

            pdf_payloads.append(
                RawSheetPayload(
                    source_filename=path.name,
                    sheet_name=f"Page_{page_idx}",
                    raw_grid=raw_grid,
                    raw_text=page_text,
                    row_count=len(raw_grid),
                    col_count=max((len(r) for r in raw_grid), default=0),
                    detected_type=assigned_type
                )
            )

    return pdf_payloads