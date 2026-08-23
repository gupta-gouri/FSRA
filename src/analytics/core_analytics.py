"""Vectorized Core Financial Analytics: 
    1. YoY Horizontal
    2. Common-Size Vertical
    3. 11 Financial Ratios
    4. 6 Structural Relationship Disconnects
"""

from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
from src.schemas.manifest import StatementType
from src.schemas.statements import StandardFinancialStatement

def _statement_to_dataframe(stmt: Optional[StandardFinancialStatement]) -> pd.DataFrame:
    """Converts a StandardFinancialStatement into a pandas DataFrame indexed by standard_key."""
    if not stmt or not stmt.line_items:
        return pd.DataFrame(columns=["raw_description", "cy_value", "py_value", "row_type"]).set_index(
            pd.Index([], name = "standard_key")
        )

    records = [
        {
            "standard_key": item.standard_key,
            "raw_description": item.raw_description,
            "cy_value": float(item.cy_value) if item.cy_value is not None else np.nan,
            "py_value": float(item.py_value) if item.py_value is not None else np.nan,
            "row_type": item.row_type,
        }
        for item in stmt.line_items
    ]

    df = pd.DataFrame(records)
    return df.drop_duplicates(subset = ["standard_key"], keep = "first").set_index("standard_key")

def _get_metric(df: pd.DataFrame, key: str, col: str ="cy_value", default: float = 0.0) -> float:
    """Safely extracts a scalar float from a DataFrame indexed by standard_key."""
    if key in df.index and pd.notna(df.loc[key, col]):
        return float(df.loc[key, col])
    return default

_g = _get_metric

# =========================================================================
# 1. HORIZONTAL & VERTICAL ANALYTICS ENGINE (ANALYTICS_01 - 04, FLAG_01)
# =========================================================================

def calculate_horizontal_vertical_analysis(
        bs_stmt: Optional[StandardFinancialStatement],
        is_stmt: Optional[StandardFinancialStatement],
        threshold_dollar: float = 100000.0,
        threshold_pct: float = 10.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Computes:
    1. ANALYTICS_01: Delta $ = Current Balance - Prior Balance
    2. ANALYTICS_02: % Delta = (Delta $ / Prior Balance) * 100 (or 'New Account' if Prior == 0)
    3. ANALYTICS_03: Common-Size BS % = (Account Balance / Total Assets) * 100
    4. ANALYTICS_04: Common-Size IS % = (Account Balance / Total Revenue) * 100
    5. FLAG_01: Material Variance Flag = (|Delta $| >= T_$) AND (|% Delta| >= T_%) OR (Prior == 0 AND Current >= T_$)
    """
    bs_df = _statement_to_dataframe(bs_stmt)
    is_df = _statement_to_dataframe(is_stmt)

    frames = []
    for df, stmt_name in [(bs_df, "BALANCE_SHEET"), (is_df, "INCOME_STATEMENT")]:
        if not df.empty:
            valid = df[df["row_type"] != "HEADER"].copy()
            valid["statement"] = stmt_name
            frames.append(valid)

    if not frames:
        empty_yoy = pd.DataFrame(
            columns = ["standard_key", "statement", "line_item", "current_period", "prior_period", "dollar_change", "pct_change", "audit_action"]
        )
        return empty_yoy, pd.DataFrame(), pd.DataFrame()

    # ANALYTICS_01 - Horizontal
    yoy_df = pd.concat(frames)
    yoy_df["dollar_change"] = yoy_df["cy_value"] - yoy_df["py_value"]

    # ANALYTICS_02 - Horizontal
    py_abs = yoy_df["py_value"].abs()
    valid_py = py_abs > 0
    pct = np.zeros(len(yoy_df))
    pct[valid_py] = (yoy_df.loc[valid_py, "dollar_change"] / py_abs[valid_py]) * 100.0
    pct[~valid_py] = np.where(yoy_df.loc[~valid_py, "cy_value"].abs() > 0, np.nan, 0.0)
    yoy_df["pct_change"] = pct

    # FLAG_01
    cond1 = (yoy_df["dollar_change"].abs() >= threshold_dollar) & (yoy_df["pct_change"].abs() >= threshold_pct)
    cond2 = (yoy_df["py_value"] == 0.0) & (yoy_df["cy_value"].abs() >= threshold_dollar)
    yoy_df["audit_action"] = np.where(cond1 | cond2, "FLAGGED", "PASS")

    yoy_df["current_period"] = yoy_df["cy_value"].round(2)
    yoy_df["prior_period"] = yoy_df["py_value"].round(2)
    yoy_df["dollar_change"] = yoy_df["dollar_change"].round(2)
    yoy_df["pct_change"] = yoy_df["pct_change"].round(2)
    yoy_df["line_item"] = yoy_df["raw_description"]

    # ANALYTICS_03 - Vertical common-size Balance sheet
    if not bs_df.empty:
        tot_assets = _g(bs_df, "TotalAssets", col="cy_value")
        common_bs = bs_df[bs_df["row_type"] != "HEADER"].copy()
        common_bs["common_size_bs_pct"] = np.where(
            tot_assets > 0,
            (common_bs["cy_value"] / tot_assets) * 100.0,
            0.0
        ).round(2)
        common_bs["line_item"] = common_bs["raw_description"]
        common_bs["value"] = common_bs["cy_value"].round(2)
        common_bs = common_bs[["line_item", "value", "common_size_bs_pct"]].reset_index()
    else:
        common_bs = pd.DataFrame(columns = ["standard_key", "line_item", "value", "common_size_bs_pct"])

    # ANALYTICS_04 - Vertical common-size Income statement
    if not is_df.empty:
        tot_rev = _g(is_df, "Revenue", col="cy_value")
        common_is = is_df[is_df["row_type"] != "HEADER"].copy()
        common_is["common_size_is_pct"] = np.where(
            tot_rev > 0,
            (common_is["cy_value"] / tot_rev) * 100.0,
            0.0
        ).round(2)
        common_is["line_item"] = common_is["raw_description"]
        common_is["value"] = common_is["cy_value"].round(2)
        common_is = common_is[["line_item", "value", "common_size_is_pct"]].reset_index()
    else:
        common_is = pd.DataFrame(columns = ["standard_key", "line_item", "value", "common_size_is_pct"])

    return(
        yoy_df[["statement", "line_item", "current_period", "prior_period", "dollar_change", "pct_change", "audit_action"]].reset_index(),
        common_bs,
        common_is,
    )

# =========================================================================
# 2. STANDARD FINANCIAL RATIOS ENGINE (RATIO_01 to RATIO_11)
# =========================================================================

def calculate_financial_ratios(
        bs_stmt: Optional[StandardFinancialStatement],
        is_stmt: Optional[StandardFinancialStatement],
) -> pd.DataFrame:
    """Computes 11 financial ratios"""
    bs = _statement_to_dataframe(bs_stmt)
    is_df = _statement_to_dataframe(is_stmt)

    cash = _g(bs, "CashAndCashEquivalents")
    mkt_sec = _g(bs, "MarketableSecurities")
    ar = _g(bs, "AccountsReceivable")
    inv = _g(bs, "Inventories")
    ap = _g(bs, "AccountsPayable")
    ca = _g(bs, "TotalCurrentAssets", default = cash + mkt_sec + ar + inv)
    cl = _g(bs, "TotalCurrentLiabilities", default = 1.0)
    st_debt = _g(bs, "ShortTermDebt")
    lt_debt = _g(bs, "LongTermDebt")
    tot_deb = st_debt + lt_debt
    tot_eq = _g(bs, "TotalStockholdersEquity", default = 1.0)

    rev = _g(is_df, "Revenue", default = 1.0)
    cogs = abs(_g(is_df, "CostOfGoodsSold"))
    ebit = _g(is_df, "OperatingIncome")
    interest_exp = abs(_g(is_df, "InterestExpense"))
    tax_exp = abs(_g(is_df, "IncomeTaxExpense"))
    ebt = _g(is_df, "EarningsBeforeTax", default = ebit - interest_exp)

    ### 1. Liquidity & Solvency ratio
    # RATIO_01: Current Ratio
    curr_ratio = ca / cl if cl > 0 else 0.0

    # RATIO_02: Quick Ratio (Acid-test)
    quick_ratio = (cash + mkt_sec + ar) / cl if cl > 0 else 0.0

    # RATIO_03: Debt_to_equity ratio
    de_ratio = tot_deb / tot_eq if tot_eq != 0 else 0.0

    # RATIO_04: Interest Coverage ratio
    int_cov = ebit / interest_exp if interest_exp > 0 else 99.0

    ### 2. Activity & Working Captial Efficiency Ratios
    # RATIO_05 - Days Sales Outstanding (DSO)
    dso = (ar / rev * 365.0) if rev > 0 else 0.0

    # RATIO_06 - Days Inventory Outstanding (DIO)
    dio = (inv / cogs * 365.0) if cogs > 0 else 0.0

    # RATIO_07 - Days Payable Outstanding (DPO)
    dpo = (ap / cogs * 365.0) if cogs > 0 else 0.0

    # RATIO_08 - Cash Conversion Cycle (CCC)
    ccc = dso + dio - dpo

    ### 3. Profitability & Operational Margins
    # RATIO_09 - Gross Profit Margin
    gp_margin = ((rev - cogs) / rev * 100.0) if rev > 0 else 0.0

    # RATIO_10 - Operating Profit Margin
    op_margin = ((ebit / rev * 100.0)) if rev > 0 else 0.0

    # RATIO_11 - Effective Tax Rate
    eff_tax_rate = (tax_exp / ebt * 100.0) if ebt > 0 else 0.0

    ratios = [
        {"rule_id": "RATIO_01", "category": "Liquidity & Solvency", "ratio_name": "Current Ratio", "formula": "Total Current Assets / Total Current Liabilities", "value": round(curr_ratio, 2), "formatted": f"{curr_ratio:.2f}x"},
        {"rule_id": "RATIO_02", "category": "Liquidity & Solvency", "ratio_name": "Quick Ratio (Acid-Test)", "formula": "(Cash + Mkt Sec + AR) / Total Current Liabilities", "value": round(quick_ratio, 2), "formatted": f"{quick_ratio:.2f}x"},
        {"rule_id": "RATIO_03", "category": "Liquidity & Solvency", "ratio_name": "Debt-to-Equity Ratio", "formula": "(Short-Term Debt + Long-Term Debt) / Total Equity", "value": round(de_ratio, 2), "formatted": f"{de_ratio:.2f}x"},
        {"rule_id": "RATIO_04", "category": "Liquidity & Solvency", "ratio_name": "Interest Coverage Ratio", "formula": "EBIT / Interest Expense", "value": round(int_cov, 2), "formatted": f"{int_cov:.2f}x"},
        {"rule_id": "RATIO_05", "category": "Activity & Working Capital", "ratio_name": "Days Sales Outstanding (DSO)", "formula": "(AR / Revenue) * 365", "value": round(dso, 1), "formatted": f"{dso:.1f} Days"},
        {"rule_id": "RATIO_06", "category": "Activity & Working Capital", "ratio_name": "Days Inventory Outstanding (DIO)", "formula": "(Inventory / COGS) * 365", "value": round(dio, 1), "formatted": f"{dio:.1f} Days"},
        {"rule_id": "RATIO_07", "category": "Activity & Working Capital", "ratio_name": "Days Payable Outstanding (DPO)", "formula": "(Accounts Payable / COGS) * 365", "value": round(dpo, 1), "formatted": f"{dpo:.1f} Days"},
        {"rule_id": "RATIO_08", "category": "Activity & Working Capital", "ratio_name": "Cash Conversion Cycle (CCC)", "formula": "DIO + DSO - DPO", "value": round(ccc, 1), "formatted": f"{ccc:.1f} Days"},
        {"rule_id": "RATIO_09", "category": "Profitability & Margins", "ratio_name": "Gross Profit Margin", "formula": "((Revenue - COGS) / Revenue) * 100", "value": round(gp_margin, 2), "formatted": f"{gp_margin:.2f}%"},
        {"rule_id": "RATIO_10", "category": "Profitability & Margins", "ratio_name": "Operating Profit Margin", "formula": "(Operating Income / Revenue) * 100", "value": round(op_margin, 2), "formatted": f"{op_margin:.2f}%"},
        {"rule_id": "RATIO_11", "category": "Profitability & Margins", "ratio_name": "Effective Tax Rate", "formula": "(Income Tax Expense / EBT) * 100", "value": round(eff_tax_rate, 2), "formatted": f"{eff_tax_rate:.2f}%"},
    ]

    return pd.DataFrame(ratios)

# =========================================================================
# 3. UNIVERSAL RELATIONSHIP DISCONNECT RULES (REL_01 to REL_06)
# =========================================================================

def evaluate_relationship_disconnects(statements: Dict[StatementType, StandardFinancialStatement],) -> pd.DataFrame:
    """
    Executes the 6 Relationship Disconnect checks:
      - REL_01: %Delta(AR) - %Delta(Revenue) > 20.0%
      - REL_02: %Delta(Revenue) - %Delta(COGS) > 15.0%
      - REL_03: %Delta(Inventory) - %Delta(COGS) > 25.0%
      - REL_04: Delta$(PP&E Net) > 0 AND Delta$(Depreciation Expense) < 0
      - REL_05: Delta$(Total Debt) > 0 AND Delta$(Interest Expense) < 0
      - REL_06: Delta$(EBT) > 0 AND Delta$(Income Tax Expense) < 0
    """

    bs = _statement_to_dataframe(statements.get(StatementType.BALANCE_SHEET))
    is_df = _statement_to_dataframe(statements.get(StatementType.INCOME_STATEMENT))

    def _pct_chg(df: pd.DataFrame, key: str) -> float:
        cy = _g(df, key, col = "cy_value")
        py = _g(df, key, col = "py_value", default = cy)
        return ((cy-py) / abs(py) * 100.0) if abs(py) > 0 else 0.0

    def _dollar_chg(df: pd.DataFrame, key: str) -> float:
        return _g(df, key, col = "cy_value") - _g(df, key, col = "py_value")

    # Percentage changes
    pct_rev = _pct_chg(is_df, "Revenue")
    pct_ar = _pct_chg(bs, "AccountsReceivable")
    pct_cogs = _pct_chg(is_df, "CostOfGoodsSold")
    pct_inv = _pct_chg(bs, "Inventories")

    # Dollar changes
    d_ppe = _dollar_chg(bs, "PropertyPlantAndEquipmentNet")
    d_depr = _dollar_chg(is_df, "DepreciationAndAmortizationExpense")
    d_st_debt = _dollar_chg(bs, "ShortTermDebt")
    d_lt_debt = _dollar_chg(bs, "LongTermDebt")
    d_tot_debt = d_st_debt + d_lt_debt
    d_interest = _dollar_chg(is_df, "InterestExpense")
    d_ebt = _dollar_chg(is_df, "EarningsBeforeTax")
    d_tax = _dollar_chg(is_df, "IncomeTaxExpense")

    disconnects = []

    # REL_01: Revenue vs. Accounts Receivable Growth Disconnect
    spread_01 = pct_ar - pct_rev
    rel_01_fail = spread_01 > 20.0
    disconnects.append({
        "rule_id": "REL_01",
        "rule_name": "Revenue vs. Accounts Receivable Growth Disconnect",
        "condition": "%Delta(AR) - %Delta(Revenue) > 20.0%",
        "metric_value": round(spread_01, 2),
        "threshold": 20.0,
        "status": "FAIL" if rel_01_fail else "PASS",
        "audit_implication": "Premature revenue recognition, unrecorded sales returns, or under-provisioning of credit losses.",
    })

    # REL_02: Revenue vs. COGS Expansion Disconnect
    spread_02 = pct_rev - pct_cogs
    rel_02_fail = spread_02 > 15.0
    disconnects.append({
        "rule_id": "REL_02",
        "rule_name": "Revenue vs. COGS Expansion Disconnect",
        "condition": "%Delta(Revenue) - %Delta(COGS) > 15.0%",
        "metric_value": round(spread_02, 2),
        "threshold": 15.0,
        "status": "FAIL" if rel_02_fail else "PASS",
        "audit_implication": "Unrecorded purchases, inventory misstatement, or aggressive margin inflation.",
    })

    # REL_03: Inventory vs. COGS Growth Disconnect
    spread_03 = pct_inv - pct_cogs
    rel_03_fail = spread_03 > 25.0
    disconnects.append({
        "rule_id": "REL_03",
        "rule_name": "Inventory vs. COGS Growth Disconnect",
        "condition": "%Delta(Inventory) - %Delta(COGS) > 25.0%",
        "metric_value": round(spread_03, 2),
        "threshold": 25.0,
        "status": "FAIL" if rel_03_fail else "PASS",
        "audit_implication": "Slow-moving or obsolete inventory, or improper capitalization of period expenses.",
    })

    # REL_04: CapEx / PP&E Expansion vs. Depreciation Inversion
    rel_04_fail = (d_ppe > 0) and (d_depr < 0)
    disconnects.append({
        "rule_id": "REL_04",
        "rule_name": "CapEx / PP&E Expansion vs. Depreciation Inversion",
        "condition": "Delta$(PP&E Net) > 0 AND Delta$(Depreciation Expense) < 0",
        "metric_value": f"PP&E: {d_ppe:+,.2f}, Depr: {d_depr:+,.2f}",
        "threshold": "Delta$(Depr) >= 0",
        "status": "FAIL" if rel_04_fail else "PASS",
        "audit_implication": "Omitted depreciation expense, improper useful-life extensions, or unrecorded asset retirements.",
    })

    # REL_05: Debt Incurrence vs. Interest Expense Inversion
    rel_05_fail = (d_tot_debt > 0) and (d_interest < 0)
    disconnects.append({
        "rule_id": "REL_05",
        "rule_name": "Debt Incurrence vs. Interest Expense Inversion",
        "condition": "Delta$(Total Debt) > 0 AND Delta$(Interest Expense) < 0",
        "metric_value": f"Debt: {d_tot_debt:+,.2f}, Interest: {d_interest:+,.2f}",
        "threshold": "Delta$(Interest) >= 0",
        "status": "FAIL" if rel_05_fail else "PASS",
        "audit_implication": "Unrecorded interest expense, unaccrued interest liabilities, or misclassified loan fees.",
    })

    # REL_06: Profit Growth vs. Tax Expense Inversion
    rel_06_fail = (d_ebt > 0) and (d_tax < 0)
    disconnects.append({
        "rule_id": "REL_06",
        "rule_name": "Profit Growth vs. Tax Expense Inversion",
        "condition": "Delta$(EBT) > 0 AND Delta$(Income Tax Expense) < 0",
        "metric_value": f"EBT: {d_ebt:+,.2f}, Tax: {d_tax:+,.2f}",
        "threshold": "Delta$(Tax) >= 0",
        "status": "FAIL" if rel_06_fail else "PASS",
        "audit_implication": "Understated income tax provision or unrecorded tax liabilities.",
    })

    return pd.DataFrame(disconnects)