import pandas as pd
import numpy as np
import pytest

from src.analytics.forecast import (
    forecast_driver_based_3_statement,
    forecast_holt_winters,
    forecast_arima_sarimax,
    run_monte_carlo_simulation,
)


def test_forecast_driver_based_3_statement_defaults():
    base_data = {
        "revenue": 10000000.0,
        "ppe_net": 4000000.0,
        "retained_earnings": 2000000.0,
        "common_stock": 3000000.0,
        "long_term_debt": 2000000.0,
        "short_term_debt": 300000.0,
        "accrued_expenses": 200000.0,
        "intangible_assets": 500000.0,
    }
    df = forecast_driver_based_3_statement(base_data, forecast_years=3)

    assert not df.empty
    assert len(df) == 3
    assert "revenue" in df.columns
    assert "net_income" in df.columns
    assert "total_assets" in df.columns
    assert "total_liabilities" in df.columns

    # Verify Assets balance (Total Assets == Total Liabilities + Total Equity)
    for _, row in df.iterrows():
        assert pytest.approx(row["total_assets"], abs=1.0) == (row["total_liabilities"] + row["total_equity"])


def test_forecast_holt_winters():
    series = [100.0, 112.0, 125.0, 138.0, 152.0, 168.0, 185.0, 202.0]
    res = forecast_holt_winters(series, forecast_periods=3, trend="add")

    assert "forecast" in res
    assert len(res["forecast"]) == 3
    assert "fitted_values" in res
    assert res["model"] == "Holt-Winters Exponential Smoothing"


def test_forecast_arima_sarimax():
    series = [100.0, 105.0, 110.0, 118.0, 125.0, 133.0, 142.0, 150.0]
    res = forecast_arima_sarimax(series, forecast_periods=3, order=(1, 1, 0))

    assert "forecast" in res
    assert len(res["forecast"]) == 3
    assert "confidence_interval_95" in res
    assert "lower_bound" in res["confidence_interval_95"]
    assert "upper_bound" in res["confidence_interval_95"]


def test_run_monte_carlo_simulation():
    res = run_monte_carlo_simulation(
        base_revenue=10000000.0,
        mean_growth=0.08,
        volatility=0.04,
        num_simulations=500,
        forecast_years=3
    )

    assert res["num_simulations"] == 500
    assert res["forecast_horizon_years"] == 3
    assert "revenue_forecast_distribution" in res
    assert "operating_income_distribution" in res
    assert "value_at_risk_5pct" in res["operating_income_distribution"]
