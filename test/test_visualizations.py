from decimal import Decimal
import pandas as pd
import pytest

from src.analytics.visualizations import (
    plot_cash_flow_waterfall,
    plot_ccc_breakdown,
    plot_cash_runway_gauge,
    plot_yoy_tornado_chart,
    plot_common_size_stacked,
    plot_bva_matrix,
    plot_benfords_law_curve,
    plot_altman_beneish_risk_bands,
    plot_operational_disconnects,
    plot_dupont_sunburst,
)


def test_plot_cash_flow_waterfall():
    res = plot_cash_flow_waterfall(
        beg_cash=100.0,
        ocf=150.0,
        icf=-50.0,
        fcf=-20.0,
        end_cash=180.0,
    )
    assert isinstance(res, dict)
    assert "data" in res
    assert "layout" in res


def test_plot_ccc_breakdown():
    res = plot_ccc_breakdown(dio=90.0, dso=60.0, dpo=45.0)
    assert isinstance(res, dict)
    assert "data" in res
    assert "layout" in res
    assert len(res["data"]) == 4


def test_plot_cash_runway_gauge():
    res_normal = plot_cash_runway_gauge(cash_balance=120000.0, monthly_burn=10000.0)
    assert isinstance(res_normal, dict)
    assert "data" in res_normal

    res_zero_burn = plot_cash_runway_gauge(cash_balance=100000.0, monthly_burn=0.0)
    assert isinstance(res_zero_burn, dict)


def test_plot_yoy_tornado_chart():
    yoy_df = pd.DataFrame([
        {"line_item": "Revenue", "pct_change": 25.0},
        {"line_item": "COGS", "pct_change": -10.0},
        {"line_item": "Operating Expenses", "pct_change": 5.0},
    ])
    res = plot_yoy_tornado_chart(yoy_df)
    assert isinstance(res, dict)
    assert "data" in res

    empty_res = plot_yoy_tornado_chart(pd.DataFrame())
    assert isinstance(empty_res, dict)


def test_plot_common_size_stacked():
    common_bs = pd.DataFrame([
        {"line_item": "Cash", "common_size_bs_pct": 10.0},
        {"line_item": "AR", "common_size_bs_pct": 20.0},
        {"line_item": "Inventory", "common_size_bs_pct": 15.0},
        {"line_item": "PP&E", "common_size_bs_pct": 55.0},
    ])
    res = plot_common_size_stacked(common_bs)
    assert isinstance(res, dict)
    assert "data" in res

    empty_res = plot_common_size_stacked(pd.DataFrame())
    assert isinstance(empty_res, dict)


def test_plot_bva_matrix():
    actuals = {"Revenue": 1050.0, "COGS": 600.0, "OpEx": 250.0}
    budget = {"Revenue": 1000.0, "COGS": 620.0, "OpEx": 240.0}

    res = plot_bva_matrix(actuals, budget)
    assert isinstance(res, dict)
    assert "data" in res


def test_plot_benfords_law_curve():
    benford_dict = {
        "overall_status": "PASS",
        "distribution_breakdown": [
            {"digit": 1, "observed_pct": 30.1, "benford_expected_pct": 30.1},
            {"digit": 2, "observed_pct": 17.6, "benford_expected_pct": 17.6},
            {"digit": 3, "observed_pct": 12.5, "benford_expected_pct": 12.5},
        ]
    }
    res = plot_benfords_law_curve(benford_dict)
    assert isinstance(res, dict)
    assert "data" in res

    empty_res = plot_benfords_law_curve({})
    assert empty_res == {}


def test_plot_altman_beneish_risk_bands():
    res = plot_altman_beneish_risk_bands(z_score=3.5, m_score=-2.5)
    assert isinstance(res, dict)
    assert "data" in res
    assert "layout" in res


def test_plot_operational_disconnects():
    rel_df = pd.DataFrame([
        {"rule_id": "REL_01", "status": "PASS"},
        {"rule_id": "REL_02", "status": "FAIL"},
        {"rule_id": "REL_03", "status": "PASS"},
    ])
    res = plot_operational_disconnects(rel_df)
    assert isinstance(res, dict)
    assert "data" in res

    empty_res = plot_operational_disconnects(pd.DataFrame())
    assert isinstance(empty_res, dict)


def test_plot_dupont_sunburst():
    dupont_dict = {
        "roe_calculated": "28.8%",
        "5_stage_dupont": {
            "tax_burden": 0.8,
            "interest_burden": 0.9,
            "operating_margin": "20.0%",
            "asset_turnover": 1.0,
            "equity_multiplier": 2.0,
        }
    }
    res = plot_dupont_sunburst(dupont_dict)
    assert isinstance(res, dict)
    assert "data" in res
