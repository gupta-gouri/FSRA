import pandas as pd
import numpy as np
import pytest

from backend.src.analytics.historical_analytics import HistoricalAnalyticsEngine


def create_sample_historical_df():
    data = [
        {
            "fiscal_year": 2021,
            "revenue": 1000.0,
            "cogs": 600.0,
            "gross_profit": 400.0,
            "opex": 200.0,
            "operating_income": 200.0,
            "depreciation_amortization": 30.0,
            "tax_expense": 35.0,
            "net_income": 135.0,
            "cash": 100.0,
            "accounts_receivable": 150.0,
            "inventory": 120.0,
            "accounts_payable": 80.0,
            "ppe_net": 400.0,
            "total_assets": 1000.0,
            "total_equity": 600.0,
            "operating_cash_flow": 160.0,
            "capex": 50.0,
        },
        {
            "fiscal_year": 2022,
            "revenue": 1150.0,
            "cogs": 670.0,
            "gross_profit": 480.0,
            "opex": 220.0,
            "operating_income": 260.0,
            "depreciation_amortization": 35.0,
            "tax_expense": 45.0,
            "net_income": 180.0,
            "cash": 140.0,
            "accounts_receivable": 170.0,
            "inventory": 135.0,
            "accounts_payable": 95.0,
            "ppe_net": 430.0,
            "total_assets": 1150.0,
            "total_equity": 720.0,
            "operating_cash_flow": 210.0,
            "capex": 60.0,
        },
        {
            "fiscal_year": 2023,
            "revenue": 1300.0,
            "cogs": 740.0,
            "gross_profit": 560.0,
            "opex": 240.0,
            "operating_income": 320.0,
            "depreciation_amortization": 40.0,
            "tax_expense": 55.0,
            "net_income": 225.0,
            "cash": 190.0,
            "accounts_receivable": 190.0,
            "inventory": 150.0,
            "accounts_payable": 110.0,
            "ppe_net": 470.0,
            "total_assets": 1300.0,
            "total_equity": 860.0,
            "operating_cash_flow": 270.0,
            "capex": 70.0,
        },
    ]
    return pd.DataFrame(data)


def test_calculate_cagr():
    df = create_sample_historical_df()
    engine = HistoricalAnalyticsEngine(df)

    cagr = engine.calculate_cagr()
    assert "revenue_cagr" in cagr
    # Revenue: (1300 / 1000) ** (1/2) - 1 = 1.3 ** 0.5 - 1 = 14.02%
    assert cagr["revenue_cagr"] == pytest.approx(14.02, abs=0.1)


def test_calculate_bps_margin_swings():
    df = create_sample_historical_df()
    engine = HistoricalAnalyticsEngine(df)

    swings_df = engine.calculate_bps_margin_swings()
    assert not swings_df.empty
    assert "gross_margin_bps_swing" in swings_df.columns
    assert len(swings_df) == 3


def test_calculate_multi_year_ccc():
    df = create_sample_historical_df()
    engine = HistoricalAnalyticsEngine(df)

    ccc_df = engine.calculate_multi_year_ccc()
    assert not ccc_df.empty
    assert "ccc_net_days" in ccc_df.columns
    assert len(ccc_df) == 3


def test_calculate_asset_intensity():
    df = create_sample_historical_df()
    engine = HistoricalAnalyticsEngine(df)

    intensity_df = engine.calculate_asset_intensity()
    assert not intensity_df.empty
    assert "fixed_asset_turnover" in intensity_df.columns
    assert len(intensity_df) == 3


def test_calculate_historical_fcff():
    df = create_sample_historical_df()
    engine = HistoricalAnalyticsEngine(df)

    fcff_df = engine.calculate_historical_fcff()
    assert not fcff_df.empty
    assert "fcff" in fcff_df.columns
    assert len(fcff_df) == 3


def test_calculate_cash_conversion_efficacy():
    df = create_sample_historical_df()
    engine = HistoricalAnalyticsEngine(df)

    efficacy_df = engine.calculate_cash_conversion_efficacy()
    assert not efficacy_df.empty
    assert "fcf_to_ebitda_efficacy_pct" in efficacy_df.columns


def test_generate_full_historical_report():
    df = create_sample_historical_df()
    engine = HistoricalAnalyticsEngine(df)

    report = engine.generate_full_historical_report()
    assert "cagr_metrics" in report
    assert "margin_bps_swings" in report
    assert "working_capital_ccc_trends" in report
    assert "asset_intensity_trends" in report
    assert "fcff_historical" in report
    assert "cash_conversion_efficacy" in report
