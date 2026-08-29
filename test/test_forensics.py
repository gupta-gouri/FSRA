from decimal import Decimal
import pytest

from backend.src.schemas.manifest import StatementType
from backend.src.schemas.statements import StandardFinancialStatement, StandardLineItem
from backend.src.analytics.forensics import (
    compute_altman_z_score,
    compute_beneish_m_score,
    compute_sloan_accrual_ratio,
    compute_dupont_roe_breakdown,
    compute_benfords_law_analysis,
)


def create_sample_bs(
    cash=100.0,
    ar=200.0,
    inv=150.0,
    ca=450.0,
    ppe=350.0,
    tot_assets=1000.0,
    ap=100.0,
    st_debt=50.0,
    cl=150.0,
    lt_debt=200.0,
    tot_liab=350.0,
    re=300.0,
    tot_eq=650.0,
    py_assets=900.0,
    py_ar=180.0,
    py_ca=400.0,
    py_ppe=300.0,
    py_cl=140.0,
    py_lt_debt=180.0,
):
    line_items = [
        StandardLineItem(standard_key="CashAndCashEquivalents", raw_description="Cash", cy_value=Decimal(str(cash)), py_value=Decimal("80.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="AccountsReceivable", raw_description="AR", cy_value=Decimal(str(ar)), py_value=Decimal(str(py_ar)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="Inventories", raw_description="Inventories", cy_value=Decimal(str(inv)), py_value=Decimal("120.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalCurrentAssets", raw_description="Total CA", cy_value=Decimal(str(ca)), py_value=Decimal(str(py_ca)), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="PropertyPlantAndEquipmentNet", raw_description="PP&E Net", cy_value=Decimal(str(ppe)), py_value=Decimal(str(py_ppe)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalAssets", raw_description="Total Assets", cy_value=Decimal(str(tot_assets)), py_value=Decimal(str(py_assets)), row_type="TOTAL"),
        StandardLineItem(standard_key="AccountsPayable", raw_description="AP", cy_value=Decimal(str(ap)), py_value=Decimal("90.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="ShortTermDebt", raw_description="ST Debt", cy_value=Decimal(str(st_debt)), py_value=Decimal("40.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalCurrentLiabilities", raw_description="Total CL", cy_value=Decimal(str(cl)), py_value=Decimal(str(py_cl)), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="LongTermDebt", raw_description="LT Debt", cy_value=Decimal(str(lt_debt)), py_value=Decimal(str(py_lt_debt)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalLiabilities", raw_description="Total Liabilities", cy_value=Decimal(str(tot_liab)), py_value=Decimal("320.0"), row_type="TOTAL"),
        StandardLineItem(standard_key="RetainedEarnings", raw_description="Retained Earnings", cy_value=Decimal(str(re)), py_value=Decimal("250.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalStockholdersEquity", raw_description="Total Equity", cy_value=Decimal(str(tot_eq)), py_value=Decimal("580.0"), row_type="TOTAL"),
    ]
    return StandardFinancialStatement(
        statement_type=StatementType.BALANCE_SHEET,
        line_items=line_items,
    )


def create_sample_is(
    rev=1000.0,
    cogs=600.0,
    ebit=200.0,
    interest=20.0,
    ebt=180.0,
    tax=36.0,
    net_inc=144.0,
    sga=100.0,
    depr=30.0,
    py_rev=900.0,
    py_cogs=540.0,
    py_sga=90.0,
    py_depr=25.0,
):
    line_items = [
        StandardLineItem(standard_key="Revenue", raw_description="Revenue", cy_value=Decimal(str(rev)), py_value=Decimal(str(py_rev)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="CostOfGoodsSold", raw_description="COGS", cy_value=Decimal(str(cogs)), py_value=Decimal(str(py_cogs)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="OperatingIncome", raw_description="EBIT", cy_value=Decimal(str(ebit)), py_value=Decimal("170.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="SellingGeneralAndAdministrative", raw_description="SG&A", cy_value=Decimal(str(sga)), py_value=Decimal(str(py_sga)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="DepreciationAndAmortizationExpense", raw_description="Depreciation", cy_value=Decimal(str(depr)), py_value=Decimal(str(py_depr)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="InterestExpense", raw_description="Interest", cy_value=Decimal(str(interest)), py_value=Decimal("18.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="EarningsBeforeTax", raw_description="EBT", cy_value=Decimal(str(ebt)), py_value=Decimal("152.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="IncomeTaxExpense", raw_description="Tax", cy_value=Decimal(str(tax)), py_value=Decimal("30.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="NetIncome", raw_description="Net Income", cy_value=Decimal(str(net_inc)), py_value=Decimal("122.0"), row_type="TOTAL"),
    ]
    return StandardFinancialStatement(
        statement_type=StatementType.INCOME_STATEMENT,
        line_items=line_items,
    )


def create_sample_cfs(cfo=150.0, cfi=-50.0):
    line_items = [
        StandardLineItem(standard_key="OperatingCashFlow", raw_description="Operating Cash Flow", cy_value=Decimal(str(cfo)), py_value=Decimal("130.0"), row_type="TOTAL"),
        StandardLineItem(standard_key="InvestingCashFlow", raw_description="Investing Cash Flow", cy_value=Decimal(str(cfi)), py_value=Decimal("-40.0"), row_type="TOTAL"),
    ]
    return StandardFinancialStatement(
        statement_type=StatementType.CASH_FLOW_STATEMENT,
        line_items=line_items,
    )


# =========================================================================
# TESTS: Altman Z-Score
# =========================================================================

def test_compute_altman_z_score_none():
    res = compute_altman_z_score(None, None)
    assert "z_score" in res
    assert "zone" in res
    assert "risk_level" in res


def test_compute_altman_z_score_safe_zone():
    bs = create_sample_bs(ca=450.0, cl=150.0, re=300.0, tot_eq=650.0, tot_liab=350.0, tot_assets=1000.0)
    is_stmt = create_sample_is(ebit=200.0, rev=1000.0)

    # X1 = (450-150)/1000 = 0.3
    # X2 = 300/1000 = 0.3
    # X3 = 200/1000 = 0.2
    # X4 = 650/350 = 1.857
    # X5 = 1000/1000 = 1.0
    # Z = 1.2(0.3) + 1.4(0.3) + 3.3(0.2) + 0.6(1.857) + 0.999(1.0) = 0.36 + 0.42 + 0.66 + 1.114 + 0.999 = 3.553
    res = compute_altman_z_score(bs, is_stmt)
    assert res["z_score"] > 2.99
    assert res["risk_level"] == "LOW"
    assert "SAFE ZONE" in res["zone"]


def test_compute_altman_z_score_distress_zone():
    bs = create_sample_bs(ca=100.0, cl=400.0, re=-200.0, tot_eq=50.0, tot_liab=950.0, tot_assets=1000.0)
    is_stmt = create_sample_is(ebit=-50.0, rev=200.0)

    res = compute_altman_z_score(bs, is_stmt)
    assert res["z_score"] < 1.81
    assert res["risk_level"] == "HIGH"
    assert "DISTRESS ZONE" in res["zone"]


# =========================================================================
# TESTS: Beneish M-Score
# =========================================================================

def test_compute_beneish_m_score_pass():
    bs = create_sample_bs()
    is_stmt = create_sample_is()
    cfs = create_sample_cfs()

    res = compute_beneish_m_score(bs, is_stmt, cfs)
    assert "m_score" in res
    assert "indices" in res
    assert res["threshold"] == -1.78
    assert res["status"].startswith("PASS")


def test_compute_beneish_m_score_flagged():
    # Setup massive receivables growth (DSRI high) and negative CFO with high net income (TATA high)
    bs = create_sample_bs(ar=800.0, py_ar=100.0)  # Massive AR spike
    is_stmt = create_sample_is(rev=1000.0, py_rev=1000.0, net_inc=500.0)
    cfs = create_sample_cfs(cfo=-300.0)  # Negative CFO

    res = compute_beneish_m_score(bs, is_stmt, cfs)
    assert res["m_score"] > -1.78
    assert "FLAGGED" in res["status"]


# =========================================================================
# TESTS: Sloan Accrual Ratio
# =========================================================================

def test_compute_sloan_accrual_ratio():
    bs = create_sample_bs(tot_assets=1000.0, py_assets=1000.0)
    is_stmt = create_sample_is(net_inc=144.0)
    cfs = create_sample_cfs(cfo=150.0, cfi=-50.0)

    # accruals = 144 - (150 + -50) = 144 - 100 = 44.0
    # avg_assets = (1000 + 1000) / 2 = 1000.0
    # ratio = (44 / 1000) * 100 = 4.4%
    res = compute_sloan_accrual_ratio(bs, is_stmt, cfs)
    assert res["accrual_dollar_value"] == 44.0
    assert res["average_total_assets"] == 1000.0
    assert res["sloan_accrual_ratio"] == "4.4%"
    assert "HIGH QUALITY" in res["earnings_quality"]


# =========================================================================
# TESTS: DuPont ROE Breakdown
# =========================================================================

def test_compute_dupont_roe_breakdown():
    bs = create_sample_bs(tot_assets=1000.0, tot_eq=500.0)
    is_stmt = create_sample_is(rev=1000.0, ebit=200.0, ebt=180.0, net_inc=144.0)

    # Net Margin = 144 / 1000 = 0.144 (14.4%)
    # Asset Turnover = 1000 / 1000 = 1.0
    # Equity Multiplier = 1000 / 500 = 2.0
    # ROE = 14.4% * 1.0 * 2.0 = 28.8%
    res = compute_dupont_roe_breakdown(bs, is_stmt)
    assert res["roe_calculated"] == "28.8%"
    assert res["3_stage_dupont"]["net_profit_margin"] == "14.4%"
    assert res["3_stage_dupont"]["asset_turnover"] == 1.0
    assert res["3_stage_dupont"]["equity_multiplier"] == 2.0
    assert res["5_stage_dupont"]["tax_burden"] == 0.8  # 144 / 180
    assert res["5_stage_dupont"]["interest_burden"] == 0.9  # 180 / 200


# =========================================================================
# TESTS: Benford's Law Analysis
# =========================================================================

def test_compute_benfords_law_insufficient_sample():
    small_bs = StandardFinancialStatement(
        statement_type=StatementType.BALANCE_SHEET,
        line_items=[
            StandardLineItem(standard_key="CashAndCashEquivalents", raw_description="Cash", cy_value=Decimal("100.0")),
            StandardLineItem(standard_key="TotalAssets", raw_description="Total Assets", cy_value=Decimal("1000.0")),
        ],
    )
    statements = {StatementType.BALANCE_SHEET: small_bs}
    # With only 2 values, sample size is < 15
    res = compute_benfords_law_analysis(statements)
    assert res["status"] == "INSUFFICIENT SAMPLE SIZE"
    assert res["sample_size"] == 2


def test_compute_benfords_law_sufficient_sample():
    bs = create_sample_bs()
    is_stmt = create_sample_is()
    cfs = create_sample_cfs()

    statements = {
        StatementType.BALANCE_SHEET: bs,
        StatementType.INCOME_STATEMENT: is_stmt,
        StatementType.CASH_FLOW_STATEMENT: cfs,
    }
    res = compute_benfords_law_analysis(statements)
    assert "overall_status" in res
    assert "chi_square_statistic" in res
    assert "mad_score" in res
    assert "distribution_breakdown" in res
    assert res["sample_size"] >= 15
