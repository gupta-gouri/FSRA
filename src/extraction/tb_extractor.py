from decimal import Decimal
from typing import Dict, List, Optional
from src.schemas.manifest import RawSheetPayload
from src.schemas.statements import StandardTrialBalance, TrialBalanceAccount, LeadSheetSummary
from src.extraction.numeric_parser import parse_financial_number
from src.extraction.lead_sheet_mapper import map_account_to_lead_sheet


def extract_trial_balance(
    payload: RawSheetPayload,
    client_name: str = "Unknown Entity",
    period_ended: str = "CY"
) -> StandardTrialBalance:
    """
    Extracts, normalizes, and groups a Trial Balance into audit lead sheets.
    """
    grid = payload.raw_grid
    if not grid or len(grid) < 2:
        return StandardTrialBalance(currency="USD", entity_name=client_name, period_ended=period_ended)

    # 1. Identify Columns (Account Number, Name, Debit, Credit / Ending Balance)
    hdr_idx = 0
    num_col, name_col, dr_col, cr_col, bal_col = None, None, None, None, None

    for r_idx, row in enumerate(grid[:5]):
        for c_idx, cell in enumerate(row):
            text = str(cell).lower().strip()
            if any(k in text for k in ["acct", "account no", "account #", "code"]):
                num_col = c_idx
                hdr_idx = r_idx
            elif any(k in text for k in ["account name", "description", "particulars", "title"]):
                name_col = c_idx
                hdr_idx = r_idx
            elif text in ["debit", "dr"]:
                dr_col = c_idx
            elif text in ["credit", "cr"]:
                cr_col = c_idx
            elif any(k in text for k in ["ending balance", "net balance", "balance"]):
                bal_col = c_idx

    # Fallbacks if columns are not explicitly labeled
    if name_col is None:
        name_col = 0 if num_col != 0 else 1
    if dr_col is None and cr_col is None and bal_col is None:
        dr_col = 1
        cr_col = 2

    accounts: List[TrialBalanceAccount] = []
    lead_sheets: Dict[str, LeadSheetSummary] = {}
    total_debits = Decimal("0.0")
    total_credits = Decimal("0.0")

    # 2. Process Account Rows
    for row in grid[hdr_idx + 1:]:
        if not row or name_col >= len(row) or row[name_col] is None:
            continue

        raw_name = str(row[name_col]).strip()
        if not raw_name or any(k in raw_name.lower() for k in ["total", "summary"]):
            continue

        raw_num = str(row[num_col]).strip() if (num_col is not None and num_col < len(row) and row[num_col]) else ""
        
        dr_val = parse_financial_number(row[dr_col]) if (dr_col is not None and dr_col < len(row)) else Decimal("0.0")
        cr_val = parse_financial_number(row[cr_col]) if (cr_col is not None and cr_col < len(row)) else Decimal("0.0")
        
        dr_val = dr_val or Decimal("0.0")
        cr_val = cr_val or Decimal("0.0")

        # Compute net ending balance
        if bal_col is not None and bal_col < len(row):
            ending_bal = parse_financial_number(row[bal_col]) or (dr_val - cr_val)
        else:
            ending_bal = dr_val - cr_val

        total_debits += dr_val
        total_credits += cr_val

        # Map to Lead Sheet
        lead_code, lead_name, fs_target = map_account_to_lead_sheet(raw_name, raw_num)

        tb_account = TrialBalanceAccount(
            account_number=raw_num if raw_num else None,
            account_name=raw_name,
            lead_sheet_code=lead_code,
            lead_sheet_name=lead_name,
            financial_statement_target=fs_target,
            debit=dr_val,
            credit=cr_val,
            ending_balance=ending_bal
        )
        accounts.append(tb_account)

        # 3. Aggregate into Lead Schedule
        if lead_code not in lead_sheets:
            lead_sheets[lead_code] = LeadSheetSummary(
                lead_code=lead_code,
                lead_name=lead_name,
                financial_statement_target=fs_target
            )

        ls = lead_sheets[lead_code]
        ls.total_debit += dr_val
        ls.total_credit += cr_val
        ls.net_balance += ending_bal
        ls.account_count += 1
        ls.accounts.append(tb_account)

    # 4. Debits == Credits Equality Check (Tolerance: 0.01)
    is_balanced = abs(total_debits - total_credits) < Decimal("0.01")

    return StandardTrialBalance(
        entity_name=client_name,
        period_ended=period_ended,
        currency="USD",
        total_debits=total_debits,
        total_credits=total_credits,
        is_balanced=is_balanced,
        accounts=accounts,
        lead_sheets=lead_sheets
    )