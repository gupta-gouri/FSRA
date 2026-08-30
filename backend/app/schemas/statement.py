from datetime import date, datetime
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict

StatementType = Literal["balance_sheet", "income_statement", "trial_balance", "cash_flow", "general_ledger"]

class LineItemBase(BaseModel):
    line_number: int
    account_code: Optional[str] = None
    account_name: str
    category: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    amount: float

class LineItemCreate(LineItemBase):
    pass

class LineItemResponse(LineItemBase):
    id: UUID
    statement_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes = True)

class StatementBase(BaseModel):
    statement_type: StatementType
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    currency: str = "USD"

class StatementCreate(StatementBase):
    project_id: UUID
    file_id: UUID

class StatementResponse(StatementBase):
    id: UUID
    project_id: UUID
    file_id: UUID
    is_balanced: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    line_items = Optional[List[LineItemResponse]] = None

    model_config = ConfigDict(from_attributes = True)