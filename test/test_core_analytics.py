from decimal import Decimal
import pandas as pd
import numpy as np
import pytest

from src.schemas.manifest import StatementType
from src.schemas.statements import StandardFinancialStatement, StandardLineItem
from src.analytics.core_analytics import (
    _statement_to_dataframe,
    _get_metric,
    _g,
    calculate_horizontal_vertical_analysis,
    calculate_financial_ratios,
    evaluate_relationship_disconnects,
)


def create_sample_bs(
    cash=100.0,
    mkt_sec=50.0,
    ar=200.0,
    inv=150.0,
    ap=100.0,
    st_debt=50.0,
    lt_debt=200.0,
    tot_assets=1000.0,
    tot_eq=500.0,
    py_ar=150.0,
    py_inv=120.0,
    py_ppe=300.0,
    cy_ppe=350.0,
):
    line_items = [
        StandardLineItem(standard_key="CashAndCashEquivalents", raw_description="Cash & Cash Equivalents", cy_value=Decimal(str(cash)), py_value=Decimal("80.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="MarketableSecurities", raw_description="Marketable Securities", cy_value=Decimal(str(mkt_sec)), py_value=Decimal("40.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="AccountsReceivable", raw_description="Accounts Receivable", cy_value=Decimal(str(ar)), py_value=Decimal(str(py_ar)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="Inventories", raw_description="Inventories", cy_value=Decimal(str(inv)), py_value=Decimal(str(py_inv)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalCurrentAssets", raw_description="Total Current Assets", cy_value=Decimal(str(cash + mkt_sec + ar + inv)), py_value=Decimal("390.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="PropertyPlantAndEquipmentNet", raw_description="PP&E Net", cy_value=Decimal(str(cy_ppe)), py_value=Decimal(str(py_ppe)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalAssets", raw_description="Total Assets", cy_value=Decimal(str(tot_assets)), py_value=Decimal("900.0"), row_type="TOTAL"),
        StandardLineItem(standard_key="AccountsPayable", raw_description="Accounts Payable", cy_value=Decimal(str(ap)), py_value=Decimal("90.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="ShortTermDebt", raw_description="Short-Term Debt", cy_value=Decimal(str(st_debt)), py_value=Decimal("40.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalCurrentLiabilities", raw_description="Total Current Liabilities", cy_value=Decimal(str(ap + st_debt)), py_value=Decimal("130.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="LongTermDebt", raw_description="Long-Term Debt", cy_value=Decimal(str(lt_debt)), py_value=Decimal("150.0"), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="TotalStockholdersEquity", raw_description="Total Equity", cy_value=Decimal(str(tot_eq)), py_value=Decimal("450.0"), row_type="TOTAL"),
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
    depr=30.0,
    py_rev=800.0,
    py_cogs=500.0,
    py_depr=25.0,
    py_interest=25.0,
    py_ebt=150.0,
    py_tax=30.0,
):
    line_items = [
        StandardLineItem(standard_key="Revenue", raw_description="Total Revenue", cy_value=Decimal(str(rev)), py_value=Decimal(str(py_rev)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="CostOfGoodsSold", raw_description="Cost of Goods Sold", cy_value=Decimal(str(cogs)), py_value=Decimal(str(py_cogs)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="OperatingIncome", raw_description="Operating Income (EBIT)", cy_value=Decimal(str(ebit)), py_value=Decimal("160.0"), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="DepreciationAndAmortizationExpense", raw_description="Depreciation Expense", cy_value=Decimal(str(depr)), py_value=Decimal(str(py_depr)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="InterestExpense", raw_description="Interest Expense", cy_value=Decimal(str(interest)), py_value=Decimal(str(py_interest)), row_type="LINE_ITEM"),
        StandardLineItem(standard_key="EarningsBeforeTax", raw_description="Earnings Before Tax", cy_value=Decimal(str(ebt)), py_value=Decimal(str(py_ebt)), row_type="SUBTOTAL"),
        StandardLineItem(standard_key="IncomeTaxExpense", raw_description="Income Tax Expense", cy_value=Decimal(str(tax)), py_value=Decimal(str(py_tax)), row_type="LINE_ITEM"),
    ]
    return StandardFinancialStatement(
        statement_type=StatementType.INCOME_STATEMENT,
        line_items=line_items,
    )


# =========================================================================
# TESTS: Helper Functions
# =========================================================================

def test_statement_to_dataframe_none_or_empty():
    df_none = _statement_to_dataframe(None)
    assert df_none.empty
    assert list(df_none.columns) == ["raw_description", "cy_value", "py_value", "row_type"]
    assert df_none.index.name == "standard_key"

    empty_stmt = StandardFinancialStatement(statement_type=StatementType.BALANCE_SHEET, line_items=[])
    df_empty = _statement_to_dataframe(empty_stmt)
    assert df_empty.empty


def test_statement_to_dataframe_valid():
    bs = create_sample_bs()
    df = _statement_to_dataframe(bs)
    assert not df.empty
    assert "CashAndCashEquivalents" in df.index
    assert df.loc["CashAndCashEquivalents", "cy_value"] == 100.0
    assert df.loc["CashAndCashEquivalents", "py_value"] == 80.0
    assert df.loc["CashAndCashEquivalents", "row_type"] == "LINE_ITEM"


def test_get_metric_and_alias():
    bs = create_sample_bs()
    df = _statement_to_dataframe(bs)

    assert _get_metric(df, "CashAndCashEquivalents") == 100.0
    assert _g(df, "CashAndCashEquivalents", col="py_value") == 80.0
    assert _get_metric(df, "NonExistentKey", default=42.0) == 42.0
    assert _g(df, "NonExistentKey") == 0.0


# =========================================================================
# TESTS: Horizontal & Vertical Analytics Engine
# =========================================================================

def test_horizontal_vertical_analysis_empty():
    yoy_df, common_bs, common_is = calculate_horizontal_vertical_analysis(None, None)
    assert yoy_df.empty
    assert common_bs.empty
    assert common_is.empty


def test_horizontal_vertical_analysis_valid():
    bs = create_sample_bs()
    is_stmt = create_sample_is()

    yoy_df, common_bs, common_is = calculate_horizontal_vertical_analysis(
        bs, is_stmt, threshold_dollar=50000.0, threshold_pct=10.0
    )

    assert not yoy_df.empty
    assert not common_bs.empty
    assert not common_is.empty

    # Check horizontal calculation for Revenue (1000 cy vs 800 py => +200 dollar change, +25% pct change)
    rev_row = yoy_df[yoy_df["standard_key"] == "Revenue"].iloc[0]
    assert rev_row["dollar_change"] == 200.0
    assert rev_row["pct_change"] == 25.0
    assert rev_row["audit_action"] == "PASS"  # dollar change 200 < threshold 50000

    # Test threshold flagging
    yoy_flagged, _, _ = calculate_horizontal_vertical_analysis(
        bs, is_stmt, threshold_dollar=100.0, threshold_pct=10.0
    )
    rev_flagged = yoy_flagged[yoy_flagged["standard_key"] == "Revenue"].iloc[0]
    assert rev_flagged["audit_action"] == "FLAGGED"

    # Common-size BS check (Cash: 100 / 1000 TotalAssets = 10%)
    cash_bs = common_bs[common_bs["standard_key"] == "CashAndCashEquivalents"].iloc[0]
    assert cash_bs["common_size_bs_pct"] == 10.0

    # Common-size IS check (COGS: 600 / 1000 Revenue = 60%)
    cogs_is = common_is[common_is["standard_key"] == "CostOfGoodsSold"].iloc[0]
    assert cogs_is["common_size_is_pct"] == 60.0


# =========================================================================
# TESTS: Financial Ratios Engine
# =========================================================================

def test_calculate_financial_ratios():
    bs = create_sample_bs(
        cash=100.0, mkt_sec=50.0, ar=200.0, inv=150.0, ap=100.0, st_debt=50.0, lt_debt=200.0, tot_eq=500.0
    )
    is_stmt = create_sample_is(
        rev=1000.0, cogs=600.0, ebit=200.0, interest=20.0, ebt=180.0, tax=36.0
    )

    ratios_df = calculate_financial_ratios(bs, is_stmt)

    assert not ratios_df.empty
    assert len(ratios_df) == 11

    ratio_dict = ratios_df.set_index("rule_id")["value"].to_dict()

    # RATIO_01: Current Ratio = (100+50+200+150) / (100+50) = 500 / 150 = 3.33
    assert ratio_dict["RATIO_01"] == pytest.approx(3.33, abs=0.01)

    # RATIO_02: Quick Ratio = (100 + 50 + 200) / 150 = 350 / 150 = 2.33
    assert ratio_dict["RATIO_02"] == pytest.approx(2.33, abs=0.01)

    # RATIO_03: Debt-to-Equity Ratio = (50 + 200) / 500 = 0.5
    assert ratio_dict["RATIO_03"] == 0.5

    # RATIO_04: Interest Coverage = 200 / 20 = 10.0
    assert ratio_dict["RATIO_04"] == 10.0

    # RATIO_05: DSO = (200 / 1000) * 365 = 73.0 Days
    assert ratio_dict["RATIO_05"] == 73.0

    # RATIO_06: DIO = (150 / 600) * 365 = 91.25 Days => rounded to 91.3 or 91.2
    assert ratio_dict["RATIO_06"] == pytest.approx(91.25, abs=0.1)

    # RATIO_07: DPO = (100 / 600) * 365 = 60.83 Days => 60.8
    assert ratio_dict["RATIO_07"] == pytest.approx(60.8, abs=0.1)

    # RATIO_08: CCC = DSO + DIO - DPO = 73.0 + 91.25 - 60.83 = 103.4
    assert ratio_dict["RATIO_08"] == pytest.approx(103.4, abs=0.2)

    # RATIO_09: Gross Margin = ((1000 - 600) / 1000) * 100 = 40.0%
    assert ratio_dict["RATIO_09"] == 40.0

    # RATIO_10: Operating Margin = (200 / 1000) * 100 = 20.0%
    assert ratio_dict["RATIO_10"] == 20.0

    # RATIO_11: Effective Tax Rate = (36 / 180) * 100 = 20.0%
    assert ratio_dict["RATIO_11"] == 20.0


# =========================================================================
# TESTS: Relationship Disconnect Rules
# =========================================================================

def test_evaluate_relationship_disconnects_all_pass():
    # Setup values so all 6 relationship checks PASS
    # AR growth: (200 - 180)/180 = 11.1%, Rev growth: (1000 - 900)/900 = 11.1% => Spread = 0% <= 20%
    # COGS growth: (600 - 540)/540 = 11.1% => Rev - COGS spread = 0% <= 15%
    # Inv growth: (150 - 135)/135 = 11.1% => Inv - COGS spread = 0% <= 25%
    # PP&E change: 350 - 300 = +50, Depr change: 30 - 25 = +5 (Not inverted)
    # Debt change: 250 - 200 = +50, Interest change: 20 - 15 = +5 (Not inverted)
    # EBT change: 180 - 150 = +30, Tax change: 36 - 30 = +6 (Not inverted)

    bs = create_sample_bs(ar=200.0, py_ar=180.0, inv=150.0, py_inv=135.0, cy_ppe=350.0, py_ppe=300.0, st_debt=50.0, lt_debt=200.0)
    is_stmt = create_sample_is(rev=1000.0, py_rev=900.0, cogs=600.0, py_cogs=540.0, depr=30.0, py_depr=25.0, interest=20.0, py_interest=15.0, ebt=180.0, py_ebt=150.0, tax=36.0, py_tax=30.0)

    statements = {StatementType.BALANCE_SHEET: bs, StatementType.INCOME_STATEMENT: is_stmt}
    disc_df = evaluate_relationship_disconnects(statements)

    assert not disc_df.empty
    assert len(disc_df) == 6
    assert (disc_df["status"] == "PASS").all()


def test_evaluate_relationship_disconnects_failures():
    # REL_01 FAIL: %Delta(AR) [100%] - %Delta(Rev) [0%] = 100% > 20%
    # REL_02 FAIL: %Delta(Rev) [50%] - %Delta(COGS) [0%] = 50% > 15%
    # REL_03 FAIL: %Delta(Inv) [100%] - %Delta(COGS) [0%] = 100% > 25%
    # REL_04 FAIL: Delta$(PP&E) [+50] > 0 AND Delta$(Depr) [-10] < 0
    # REL_05 FAIL: Delta$(Debt) [+50] > 0 AND Delta$(Interest) [-5] < 0
    # REL_06 FAIL: Delta$(EBT) [+30] > 0 AND Delta$(Tax) [-5] < 0

    bs = create_sample_bs(
        ar=200.0, py_ar=100.0,        # AR +100%
        inv=200.0, py_inv=100.0,      # Inv +100%
        cy_ppe=350.0, py_ppe=300.0,   # PP&E +50
        st_debt=50.0, lt_debt=200.0   # Total Debt CY = 250 vs PY 200 (in py_debt=200)
    )
    is_stmt = create_sample_is(
        rev=1500.0, py_rev=1000.0,    # Rev +50%
        cogs=600.0, py_cogs=600.0,    # COGS 0%
        depr=15.0, py_depr=25.0,      # Depr -10
        interest=15.0, py_interest=20.0, # Interest -5
        ebt=180.0, py_ebt=150.0,      # EBT +30
        tax=25.0, py_tax=30.0         # Tax -5
    )

    statements = {StatementType.BALANCE_SHEET: bs, StatementType.INCOME_STATEMENT: is_stmt}
    disc_df = evaluate_relationship_disconnects(statements)

    assert not disc_df.empty
    status_map = disc_df.set_index("rule_id")["status"].to_dict()

    assert status_map["REL_01"] == "FAIL"
    assert status_map["REL_02"] == "FAIL"
    assert status_map["REL_03"] == "FAIL"
    assert status_map["REL_04"] == "FAIL"
    assert status_map["REL_05"] == "FAIL"
    assert status_map["REL_06"] == "FAIL"
