from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field

class StatementType(str, Enum):
    """Supported financial statements and schedule types."""
    BALANCE_SHEET = "BALANCE_SHEET"
    INCOME_STATEMENT = "INCOME_STATEMENT"
    CASH_FLOW_STATEMENT = "CASH_FLOW_STATEMENT"
    SOCE = "SOCE"
    TRIAL_BALANCE = "TRIAL_BALANCE"
    AR_AGING = "AR_AGING"
    PPE_SCHEDULE = "PPE_SCHEDULE"
    DEBT_MATURITY = "DEBT_MATURITY"
    UNKNOWN = "UNKNOWN"

class DocumentMetadata(BaseModel):
    """Metadata detected from file headers or user input."""
    client_name: str | None = None
    period_ended: str | None = None 
    currency: str | None = None
    scale: str | None = None

class RawSheetPayload(BaseModel):
    """Data container for a single worksheet parsed from an Excel file."""
    source_filename: str
    sheet_name: str
    raw_grid: List[List[Any]] = Field(default_factory = list)
    raw_text: Optional[str] = " "
    row_count: int = 0
    col_count: int = 0
    detected_type: StatementType = StatementType.UNKNOWN

class IngestionManifest(BaseModel):
    """The master container that holds all the ingested sheets from all files."""
    metadata: DocumentMetadata = Field(default_factory = DocumentMetadata)
    sheets: List[RawSheetPayload] = Field(default_factory = list)