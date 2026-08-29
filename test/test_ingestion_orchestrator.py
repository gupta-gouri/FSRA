from pathlib import Path
from decimal import Decimal
import pytest

from backend.src.schemas.manifest import StatementType, RawSheetPayload, IngestionManifest
from backend.src.schemas.statements import StandardFinancialStatement, StandardLineItem
from backend.src.ingestion.orchestrator import ingest_sources


def test_ingest_sources_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        ingest_sources(["nonexistent_file.xlsx"])


def test_ingest_sources_unsupported_format(tmp_path):
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("dummy content")

    with pytest.raises(ValueError, match="Unsupported file format"):
        ingest_sources([invalid_file])
