from decimal import Decimal
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from src.schemas.manifest import StatementType


class StandardLineItem(BaseModel):
    """Normalized line item record across financial statements."""
    standard_key: str
    raw_description: str = ""
    cy_value: Optional[Decimal] = None
    py_value: Optional[Decimal] = None
    row_type: str = "LINE"
    row_index: int = 0


class StandardFinancialStatement(BaseModel):
    """Master container for a normalized financial statement."""
    statement_type: StatementType
    entity_name: str = "Unknown Entity"
    period_ended_cy: str = "CY"
    currency: str = "USD"
    scale: Decimal = Field(default=Decimal("1.0"))
    line_items: List[StandardLineItem] = Field(default_factory=list)

    @property
    def key_map_cy(self) -> Dict[str, Decimal]:
        return {item.standard_key: item.cy_value for item in self.line_items if item.cy_value is not None}

    @property
    def key_map_py(self) -> Dict[str, Decimal]:
        return {item.standard_key: item.py_value for item in self.line_items if item.py_value is not None}

class TrialBalanceAccount(BaseModel):
    """Represents a single account line from the General Ledger / Trial Balance."""
    account_number: Optional[str] = None
    account_name: str
    lead_sheet_code: str        # e.g., "A", "B", "C", "AA", "BB"
    lead_sheet_name: str        # e.g., "Cash and cash Equivalents"
    financial_statement_target: str 
    debit: Optional[Decimal] = Decimal("0.0")
    credit: Optional[Decimal] = Decimal("0.0")
    ending_balance: Decimal = Decimal("0.0") # Debit - Credit or Credit - Debit

class LeadSheetSummary(BaseModel):
    """Aggregated roll-up for a single Audit Lead Schedule."""
    lead_code: str
    lead_name: str
    financial_statement_target: str 
    total_debit: Decimal = Decimal("0.0")
    total_credit: Decimal = Decimal("0.0")
    net_balance: Decimal = Decimal("0.0")
    account_count: int = 0
    accounts: List[TrialBalanceAccount] = Field(default_factory = list)

class StandardTrialBalance(BaseModel):
    """Container for the entire normalized Trial Balance and its Lead sheet roll-ups."""
    entity_name: Optional[str] = None
    period_ended: Optional[str] = None
    currency: str
    total_debits: Decimal = Decimal("0.0")
    total_credits: Decimal = Decimal("0.0")
    is_balanced: bool = False       # Debits == Credits check
    accounts: List[TrialBalanceAccount] = Field(default_factory = list)
    lead_sheets: Dict[str, LeadSheetSummary] = Field(default_factory = dict)