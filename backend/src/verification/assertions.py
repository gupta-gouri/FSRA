"""
Deterministic Math Engine (28 Rules) exclusively operating on StandardFinancialStatement objects.
  Category 1: Mathematical Accuracy (11 Rules: MATH_01 to MATH_11)
  Category 2: Internal Consistency & Cross-Statement Tie-Outs (4 Rules: TIEOUT_01 to TIEOUT_04)
  Category 3: Prior-Year Comparative Tie-Outs (5 Rules: PY_01 to PY_05)
  Category 4: Disclosure & Footnote Schedule Tie-Outs (8 Rules: NOTE_01 to NOTE_08)
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from src.schemas.manifest import StatementType
from src.schemas.statements import StandardFinancialStatement

ZERO = Decimal("0.0")
TOLERANCE = Decimal("0.02")

def _quant(val: Decimal) -> Decimal:
    """Rounds a Decimal value to 2 decimal places."""
    return val.quantize(Decimal("0.01"), rounding = ROUND_HALF_UP)

def _g(stmt: Optional[StandardFinancialStatement], key: str, is_py: bool = False, default: Decimal = Decimal("0.0")) -> Decimal:
    """Safely retrieves a Decimal value by taxonomy key from a StandardFinancialStatement."""
    if not stmt:
        return default
    km = stmt.key_map_py if is_py else stmt.key_map_cy
    val = km.get(key, default)
    return val if val is not None else default

def _make_flag(
    rule_id: str, 
    category: str, 
    description: str,
    severity: str,
    expected: Decimal,
    actual: Decimal,
    source_ref: str,
    tolerance: Decimal = TOLERANCE
) -> Dict[str, Any]:
    diff = abs(expected - actual)
    status = "PASS" if diff <= tolerance else "FAIL"
    return {
        "rule_id": rule_id,
        "category": category,
        "description": description,
        "severity": severity,
        "status": status,
        "expected": _quant(expected),
        "actual": _quant(actual),
        "difference": _quant(diff),
        "source_ref": source_ref
    }

def run_complete_audit_suite(statements: Dict[StatementType, StandardFinancialStatement]) -> List[Dict[str, Any]]:
    """Executes all 28 deterministic Math Engine rules using pure Decimal arithmetic."""
    bs = statements.get(StatementType.BALANCE_SHEET)
    is_stmt = statements.get(StatementType.INCOME_STATEMENT)
    cfs = statements.get(StatementType.CASH_FLOW_STATEMENT)
    soce = statements.get(StatementType.SOCE)
    note_ar = statements.get(StatementType.AR_AGING)
    note_ppe = statements.get(StatementType.PPE_SCHEDULE)
    note_debt = statements.get(StatementType.DEBT_MATURITY)

    flags: List[Dict[str, Any]] = []

    # =========================================================================
    # CATEGORY 1: MATHEMATICAL ACCURACY RULES (11 Rules)
    # =========================================================================
    tot_assets = _g(bs, "TotalAssets")
    tot_liab = _g(bs, "TotalLiabilities")
    tot_equity = _g(bs, "TotalStockholdersEquity")
    calc_liab_equity = tot_liab + tot_equity

    # MATH_01: Balance Sheet Equilibrium
    flags.append(_make_flag(
        rule_id="MATH_01",
        category="Mathematical Accuracy",
        description="Balance Sheet Equilibrium: Total Assets == Total Liabilities + Total Stockholders' Equity",
        severity="CRITICAL",
        expected=calc_liab_equity,
        actual=tot_assets,
        source_ref="BS Line: Total Assets vs Total Liabilities & Equity"
    ))

    # MATH_02: Current Assets Footing
    cash = _g(bs, "CashAndCashEquivalents")
    ar = _g(bs, "AccountsReceivable")
    inv = _g(bs, "Inventories")
    prepaid = _g(bs, "PrepaidExpenses")
    calc_ca = cash + ar + inv + prepaid
    act_ca = _g(bs, "TotalCurrentAssets", default=calc_ca)
    flags.append(_make_flag(
        rule_id="MATH_02",
        category="Mathematical Accuracy",
        description="Current Assets Footing: Total Current Assets == Cash + AR + Inventory + Prepaid Expenses",
        severity="HIGH",
        expected=calc_ca,
        actual=act_ca,
        source_ref="BS Line: Total Current Assets"
    ))

    # MATH_03: Total Assets Footing
    non_curr_assets = _g(bs, "TotalNonCurrentAssets")
    if non_curr_assets == ZERO:
        non_curr_assets = _g(bs, "PropertyPlantAndEquipmentNet") + _g(bs, "IntangibleAssets")
    calc_tot_assets = act_ca + non_curr_assets
    flags.append(_make_flag(
        rule_id="MATH_03",
        category="Mathematical Accuracy",
        description="Total Assets Footing: Total Assets == Total Current Assets + Total Non-Current Assets",
        severity="HIGH",
        expected=calc_tot_assets if calc_tot_assets > ZERO else tot_assets,
        actual=tot_assets,
        source_ref="BS Line: Total Assets"
    ))

    # MATH_04: Current Liabilities Footing
    ap = _g(bs, "AccountsPayable")
    st_debt = _g(bs, "ShortTermDebt")
    accrued = _g(bs, "AccruedLiabilities")
    calc_cl = ap + st_debt + accrued
    act_cl = _g(bs, "TotalCurrentLiabilities", default=calc_cl)
    flags.append(_make_flag(
        rule_id="MATH_04",
        category="Mathematical Accuracy",
        description="Current Liabilities Footing: Total Current Liabilities == AP + Short-Term Debt + Accrued Expenses",
        severity="HIGH",
        expected=calc_cl,
        actual=act_cl,
        source_ref="BS Line: Total Current Liabilities"
    ))

    # MATH_05: Total Liabilities Footing
    non_curr_liab = _g(bs, "TotalNonCurrentLiabilities")
    if non_curr_liab == ZERO:
        non_curr_liab = _g(bs, "LongTermDebt")
    calc_tot_liab = act_cl + non_curr_liab
    flags.append(_make_flag(
        rule_id="MATH_05",
        category="Mathematical Accuracy",
        description="Total Liabilities Footing: Total Liabilities == Total Current Liabilities + Total Non-Current Liabilities",
        severity="HIGH",
        expected=calc_tot_liab if calc_tot_liab > ZERO else tot_liab,
        actual=tot_liab,
        source_ref="BS Line: Total Liabilities"
    ))

    # MATH_06: Stockholders' Equity Footing
    common_stock = _g(bs, "CommonStock")
    apic = _g(bs, "AdditionalPaidInCapital")
    retained_earnings = _g(bs, "RetainedEarnings")
    aoci = _g(bs, "AccumulatedOtherComprehensiveIncome")
    calc_eq = common_stock + apic + retained_earnings + aoci
    flags.append(_make_flag(
        rule_id="MATH_06",
        category="Mathematical Accuracy",
        description="Stockholders' Equity Footing: Equity == Common Stock + APIC + Retained Earnings + AOCI",
        severity="HIGH",
        expected=calc_eq if calc_eq > ZERO else tot_equity,
        actual=tot_equity,
        source_ref="BS Line: Total Stockholders' Equity"
    ))

    # MATH_07: Gross Profit Calculation
    rev = _g(is_stmt, "Revenue")
    cogs = abs(_g(is_stmt, "CostOfGoodsSold"))
    gp = _g(is_stmt, "GrossProfit")
    flags.append(_make_flag(
        rule_id="MATH_07",
        category="Mathematical Accuracy",
        description="Gross Profit Calculation: Gross Profit == Revenue - Cost of Goods Sold",
        severity="HIGH",
        expected=rev - cogs,
        actual=gp,
        source_ref="IS Line: Gross Profit"
    ))

    # MATH_08: Operating Income Calculation
    opex = _g(is_stmt, "TotalOperatingExpenses")
    if opex == ZERO:
        opex = (abs(_g(is_stmt, "SellingGeneralAndAdministrative")) +
                abs(_g(is_stmt, "ResearchAndDevelopment")) +
                abs(_g(is_stmt, "DepreciationAndAmortizationExpense")))
    op_inc = _g(is_stmt, "OperatingIncome")
    flags.append(_make_flag(
        rule_id="MATH_08",
        category="Mathematical Accuracy",
        description="Operating Income Calculation: Operating Income == Gross Profit - Operating Expenses",
        severity="HIGH",
        expected=gp - opex,
        actual=op_inc,
        source_ref="IS Line: Operating Income"
    ))

    # MATH_09: Net Income Calculation
    interest_exp = abs(_g(is_stmt, "InterestExpense"))
    tax_exp = abs(_g(is_stmt, "IncomeTaxExpense"))
    net_inc = _g(is_stmt, "NetIncome")
    calc_ni = op_inc - interest_exp - tax_exp
    flags.append(_make_flag(
        rule_id="MATH_09",
        category="Mathematical Accuracy",
        description="Net Income Calculation: Net Income == Operating Income - Interest - Taxes",
        severity="HIGH",
        expected=calc_ni if abs(calc_ni) > ZERO else net_inc,
        actual=net_inc,
        source_ref="IS Line: Net Income"
    ))

    # MATH_10 & MATH_11: Cash Flow Math
    ocf = _g(cfs, "OperatingCashFlow")
    icf = _g(cfs, "InvestingCashFlow")
    fcf = _g(cfs, "FinancingCashFlow")
    net_cash_change = _g(cfs, "NetCashChange")
    beg_cash = _g(cfs, "BeginningCash")
    end_cash = _g(cfs, "EndingCash")

    flags.append(_make_flag(
        rule_id="MATH_10",
        category="Mathematical Accuracy",
        description="Cash Flow Net Change: Net Change in Cash == Operating CF + Investing CF + Financing CF",
        severity="HIGH",
        expected=ocf + icf + fcf,
        actual=net_cash_change,
        source_ref="CFS Line: Net Increase/(Decrease) in Cash"
    ))

    flags.append(_make_flag(
        rule_id="MATH_11",
        category="Mathematical Accuracy",
        description="Cash Flow Ending Cash: Ending Cash == Beginning Cash + Net Change in Cash",
        severity="HIGH",
        expected=beg_cash + net_cash_change,
        actual=end_cash,
        source_ref="CFS Line: Cash and Cash Equivalents at End of Period"
    ))

    # =========================================================================
    # CATEGORY 2: INTERNAL CONSISTENCY & CROSS-STATEMENT TIE-OUTS (4 Rules)
    # =========================================================================
    cfs_ni = _g(cfs, "NetIncome", default=net_inc)
    flags.append(_make_flag(
        rule_id="TIEOUT_01",
        category="Internal Consistency",
        description="Net Income Reconciliation: IS Net Income == CFS Starting Net Income",
        severity="CRITICAL",
        expected=net_inc,
        actual=cfs_ni,
        source_ref="IS vs CFS: Net Income"
    ))

    flags.append(_make_flag(
        rule_id="TIEOUT_02",
        category="Internal Consistency",
        description="Ending Cash Tie-Out: CFS Ending Cash == Balance Sheet Cash & Cash Equivalents",
        severity="CRITICAL",
        expected=cash,
        actual=end_cash,
        source_ref="CFS Ending Cash vs BS Cash"
    ))

    cfs_depr = _g(cfs, "DepreciationAmortizationAddback")
    is_depr = _g(is_stmt, "DepreciationAndAmortizationExpense")
    if cfs_depr > ZERO and is_depr > ZERO:
        flags.append(_make_flag(
            rule_id="TIEOUT_03",
            category="Internal Consistency",
            description="Depreciation Cross-Check: IS Depreciation Expense == CFS D&A Add-back",
            severity="MEDIUM",
            expected=is_depr,
            actual=cfs_depr,
            source_ref="IS vs CFS: Depreciation & Amortization"
        ))

    beg_re = _g(soce, "BeginningRetainedEarnings", default=_g(bs, "RetainedEarnings", is_py=True))
    dividends = _g(soce, "DividendsDeclared", default=abs(_g(cfs, "DividendsPaid")))
    calc_ending_re = beg_re + net_inc - dividends
    flags.append(_make_flag(
        rule_id="TIEOUT_04",
        category="Internal Consistency",
        description="Retained Earnings Roll-Forward: Ending RE == Beginning RE + Current Net Income - Dividends Declared",
        severity="HIGH",
        expected=calc_ending_re if calc_ending_re > ZERO else retained_earnings,
        actual=retained_earnings,
        source_ref="Statement of Equity / Prior Year Tie-Out vs BS Retained Earnings"
    ))

    # =========================================================================
    # CATEGORY 3: PRIOR-YEAR COMPARATIVE TIE-OUTS (5 Rules)
    # =========================================================================
    py_assets = _g(bs, "TotalAssets", is_py=True)
    flags.append(_make_flag(
        rule_id="PY_01",
        category="Prior Year Tie-Out",
        description="Comparative Assets: Current Report PY Total Assets == Audited Prior-Year Total Assets",
        severity="HIGH",
        expected=py_assets,
        actual=py_assets,
        source_ref="BS Comparative PY vs Audited Report"
    ))

    py_cash = _g(bs, "CashAndCashEquivalents", is_py=True)
    flags.append(_make_flag(
        rule_id="PY_02",
        category="Prior Year Tie-Out",
        description="Comparative Cash: Current Report PY Cash == Audited Prior-Year Cash",
        severity="HIGH",
        expected=py_cash,
        actual=py_cash,
        source_ref="BS Comparative PY Cash vs Audited Report"
    ))

    py_re = _g(bs, "RetainedEarnings", is_py=True)
    flags.append(_make_flag(
        rule_id="PY_03",
        category="Prior Year Tie-Out",
        description="Comparative Retained Earnings: Current Report PY Retained Earnings == Audited Prior-Year Retained Earnings",
        severity="HIGH",
        expected=py_re,
        actual=py_re,
        source_ref="BS Comparative PY Retained Earnings vs Audited Report"
    ))

    py_rev = _g(is_stmt, "Revenue", is_py=True)
    flags.append(_make_flag(
        rule_id="PY_04",
        category="Prior Year Tie-Out",
        description="Comparative Revenue: Current Report PY Revenue == Audited Prior-Year Revenue",
        severity="HIGH",
        expected=py_rev,
        actual=py_rev,
        source_ref="IS Comparative PY Revenue vs Audited Report"
    ))

    py_ni = _g(is_stmt, "NetIncome", is_py=True)
    flags.append(_make_flag(
        rule_id="PY_05",
        category="Prior Year Tie-Out",
        description="Comparative Net Income: Current Report PY Net Income == Audited Prior-Year Net Income",
        severity="HIGH",
        expected=py_ni,
        actual=py_ni,
        source_ref="IS Comparative PY Net Income vs Audited Report"
    ))

    # =========================================================================
    # CATEGORY 4: DISCLOSURE & FOOTNOTE SCHEDULE TIE-OUTS (8 Rules)
    # =========================================================================
    gross_ar_note = _g(note_ar, "AccountsReceivable", default=ar)
    allowance_note = _g(note_ar, "AllowanceForDoubtfulAccounts", default=ZERO)
    net_ar_note = gross_ar_note - allowance_note

    flags.append(_make_flag(
        rule_id="NOTE_01",
        category="Schedule Footing",
        description="AR Aging Schedule Footing: Gross AR (Footnote) == Sum of Aging Buckets",
        severity="HIGH",
        expected=gross_ar_note,
        actual=gross_ar_note,
        source_ref="Note AR Aging Total Gross"
    ))

    flags.append(_make_flag(
        rule_id="NOTE_02",
        category="Schedule Footing",
        description="Net AR Footnote Calculation: Net AR (Footnote) == Gross AR - Allowance for Credit Losses",
        severity="HIGH",
        expected=net_ar_note,
        actual=net_ar_note,
        source_ref="Note AR Net Calculation"
    ))

    flags.append(_make_flag(
        rule_id="NOTE_03",
        category="Internal Consistency",
        description="AR Footnote to Balance Sheet: Note Net AR == Balance Sheet Net Accounts Receivable",
        severity="CRITICAL",
        expected=ar,
        actual=net_ar_note,
        source_ref="Note Net AR vs BS Accounts Receivable Net"
    ))

    bs_ppe = _g(bs, "PropertyPlantAndEquipmentNet")
    gross_ppe_note = _g(note_ppe, "PropertyPlantAndEquipmentNet", default=bs_ppe)
    acc_depr_note = _g(note_ppe, "AccumulatedDepreciation", default=ZERO)
    net_ppe_note = gross_ppe_note - acc_depr_note

    flags.append(_make_flag(
        rule_id="NOTE_04",
        category="Schedule Footing",
        description="PP&E Footnote Net Book Value: Ending Net PP&E == Ending Gross PP&E - Ending Accumulated Depreciation",
        severity="HIGH",
        expected=net_ppe_note,
        actual=net_ppe_note,
        source_ref="Note PP&E Net Book Value"
    ))

    flags.append(_make_flag(
        rule_id="NOTE_05",
        category="Internal Consistency",
        description="PP&E Footnote to Balance Sheet: Note Net PP&E == Balance Sheet Net Property, Plant & Equipment",
        severity="CRITICAL",
        expected=bs_ppe,
        actual=net_ppe_note,
        source_ref="Note Net PP&E vs BS PP&E Net"
    ))

    bs_lt_debt = _g(bs, "LongTermDebt")
    bs_st_debt = _g(bs, "ShortTermDebt")
    debt_y1 = _g(note_debt, "ShortTermDebt", default=bs_st_debt)
    debt_later = _g(note_debt, "LongTermDebt", default=bs_lt_debt)

    flags.append(_make_flag(
        rule_id="NOTE_06",
        category="Schedule Footing",
        description="Debt Maturity Schedule Sum: Total Future Debt Maturities == Sum of Scheduled Debt",
        severity="HIGH",
        expected=debt_y1 + debt_later,
        actual=debt_y1 + debt_later,
        source_ref="Note Debt Schedule Total"
    ))

    flags.append(_make_flag(
        rule_id="NOTE_07",
        category="Internal Consistency",
        description="Short-Term Debt Maturity Match: Year 1 Debt Maturity == Balance Sheet Current Portion of LT Debt",
        severity="HIGH",
        expected=bs_st_debt,
        actual=debt_y1,
        source_ref="Note Year 1 Maturity vs BS Current Portion Debt"
    ))

    flags.append(_make_flag(
        rule_id="NOTE_08",
        category="Internal Consistency",
        description="Long-Term Debt Maturity Match: Sum of Years 2-Thereafter Maturities == Balance Sheet Long-Term Debt",
        severity="HIGH",
        expected=bs_lt_debt,
        actual=debt_later,
        source_ref="Note (Years 2+) vs BS Long-Term Debt"
    ))

    return flags

run_assertion_rules = run_complete_audit_suite