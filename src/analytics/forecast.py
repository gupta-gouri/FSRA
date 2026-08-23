"""
Financial Forecasting & Predictive Engine:
1. Driver-Based 3-Statement Financial Model
2. Holt-Winters Exponential Smoothing
3. ARIMA / SARIMAX Modeling
4. Monte Carlo Stochastic Simulation
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX


# =========================================================================
# 1. DRIVER-BASED 3-STATEMENT FORECASTING MODEL
# =========================================================================

def forecast_driver_based_3_statement(
    base_year_data: Dict[str, float],
    forecast_years: int = 3,
    drivers: Optional[Dict[str, float]] = None
) -> pd.DataFrame:
    """
    Builds an integrated 3-statement forecast where:
      - Income Statement drives Retained Earnings and Operating Cash Flow
      - Working capital accounts roll forward via operational turnover drivers
      - Cash acts as the Balance Sheet plug to maintain Assets == Liabilities + Equity
    """
    if drivers is None:
        drivers = {
            "revenue_growth_rate": 0.08,      # 8.0% annual revenue growth
            "cogs_pct_revenue": 0.58,         # 58.0% COGS margin
            "sga_pct_revenue": 0.16,          # 16.0% SG&A
            "rd_pct_revenue": 0.065,          # 6.5% R&D
            "tax_rate": 0.25,                 # 25.0% Effective Tax Rate
            "dso_days": 50.0,                 # Accounts Receivable Days
            "dio_days": 55.0,                 # Inventory Days
            "dpo_days": 45.0,                 # Accounts Payable Days
            "capex_pct_revenue": 0.08,        # CapEx as % of Revenue
            "depr_pct_ppe": 0.10,             # Annual Depreciation rate on Net PP&E
            "dividend_payout_ratio": 0.30     # 30.0% Dividend payout on Net Income
        }

    records = []
    
    # Starting base period balances
    curr_rev = base_year_data.get("revenue", 12800000.0)
    curr_ppe = base_year_data.get("ppe_net", 5200000.0)
    curr_re = base_year_data.get("retained_earnings", 2900000.0)
    curr_common_stock = base_year_data.get("common_stock", 3500000.0)
    curr_lt_debt = base_year_data.get("long_term_debt", 2500000.0)
    curr_st_debt = base_year_data.get("short_term_debt", 400000.0)
    curr_accrued = base_year_data.get("accrued_expenses", 350000.0)
    curr_intangibles = base_year_data.get("intangible_assets", 800000.0)

    for year_idx in range(1, forecast_years + 1):
        year_label = f"Forecast_Y{year_idx}"
        
        # --- Income Statement Projections ---
        rev = curr_rev * (1.0 + drivers["revenue_growth_rate"])
        cogs = rev * drivers["cogs_pct_revenue"]
        gross_profit = rev - cogs
        
        sga = rev * drivers["sga_pct_revenue"]
        rd = rev * drivers["rd_pct_revenue"]
        depr = curr_ppe * drivers["depr_pct_ppe"]
        total_opex = sga + rd + depr
        operating_income = gross_profit - total_opex
        
        interest_exp = (curr_lt_debt + curr_st_debt) * 0.05  # 5% cost of debt
        ebt = operating_income - interest_exp
        tax_exp = max(ebt * drivers["tax_rate"], 0.0)
        net_income = ebt - tax_exp

        # --- Cash Flow & Working Capital ---
        ar = (rev / 365.0) * drivers["dso_days"]
        inv = (cogs / 365.0) * drivers["dio_days"]
        ap = (cogs / 365.0) * drivers["dpo_days"]
        
        capex = rev * drivers["capex_pct_revenue"]
        dividends = net_income * drivers["dividend_payout_ratio"]
        
        # PP&E Roll-forward
        curr_ppe = curr_ppe + capex - depr
        # Retained Earnings Roll-forward
        curr_re = curr_re + net_income - dividends
        
        total_equity = curr_common_stock + curr_re
        total_liabilities = ap + curr_st_debt + curr_accrued + curr_lt_debt
        target_assets = total_liabilities + total_equity
        
        # Non-Cash Assets
        non_cash_assets = ar + inv + curr_ppe + curr_intangibles
        # Cash Plug to maintain Balance Sheet Equilibrium
        cash_plug = max(target_assets - non_cash_assets, 0.0)
        total_assets = non_cash_assets + cash_plug

        records.append({
            "period": year_label,
            "revenue": round(rev, 2),
            "cogs": round(cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "operating_income": round(operating_income, 2),
            "net_income": round(net_income, 2),
            "cash": round(cash_plug, 2),
            "accounts_receivable": round(ar, 2),
            "inventory": round(inv, 2),
            "ppe_net": round(curr_ppe, 2),
            "total_assets": round(total_assets, 2),
            "accounts_payable": round(ap, 2),
            "total_liabilities": round(total_liabilities, 2),
            "retained_earnings": round(curr_re, 2),
            "total_equity": round(total_equity, 2),
            "capex": round(capex, 2),
            "dividends_paid": round(dividends, 2)
        })

        curr_rev = rev

    return pd.DataFrame(records)


# =========================================================================
# 2. HOLT-WINTERS EXPONENTIAL SMOOTHING
# =========================================================================

def forecast_holt_winters(
    series: List[float],
    forecast_periods: int = 3,
    trend: str = "add",
    seasonal: Optional[str] = None,
    seasonal_periods: Optional[int] = None
) -> Dict[str, Any]:
    """
    Applies Holt-Winters exponential smoothing model to capture level, trend, and seasonality.
    """
    ts = pd.Series(series)
    
    # Select model configuration based on data availability
    if len(ts) < 4:
        # Fallback to simple exponential smoothing for short time-series
        model = ExponentialSmoothing(ts, trend=None, seasonal=None, initialization_method="estimated")
    else:
        model = ExponentialSmoothing(
            ts,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods,
            initialization_method="estimated"
        )

    fitted_model = model.fit(optimized=True)
    predictions = fitted_model.forecast(forecast_periods)

    return {
        "model": "Holt-Winters Exponential Smoothing",
        "fitted_values": [round(float(v), 2) for v in fitted_model.fittedvalues],
        "forecast": [round(float(v), 2) for v in predictions],
        "params": {
            "smoothing_level": round(float(fitted_model.params.get("smoothing_level", 0.0)), 4),
            "smoothing_trend": round(float(fitted_model.params.get("smoothing_trend", 0.0)), 4) if trend else None
        }
    }


# =========================================================================
# 3. ARIMA / SARIMAX MODELING
# =========================================================================

def forecast_arima_sarimax(
    series: List[float],
    forecast_periods: int = 3,
    order: Tuple[int, int, int] = (1, 1, 0),
    seasonal_order: Optional[Tuple[int, int, int, int]] = None
) -> Dict[str, Any]:
    """
    Fits an ARIMA / SARIMAX model and generates forecasts with 95% confidence intervals.
    """
    ts = np.array(series, dtype=float)

    if seasonal_order:
        model = SARIMAX(ts, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
    else:
        model = ARIMA(ts, order=order)

    fitted_model = model.fit()
    forecast_res = fitted_model.get_forecast(steps=forecast_periods)
    
    mean_forecast = forecast_res.predicted_mean
    conf_int = forecast_res.conf_int(alpha=0.05)

    return {
        "model": f"ARIMA{order}" if not seasonal_order else f"SARIMAX{order}x{seasonal_order}",
        "forecast": [round(float(v), 2) for v in mean_forecast],
        "confidence_interval_95": {
            "lower_bound": [round(float(v), 2) for v in conf_int[:, 0]],
            "upper_bound": [round(float(v), 2) for v in conf_int[:, 1]],
        },
        "aic": round(float(fitted_model.aic), 2),
        "bic": round(float(fitted_model.bic), 2)
    }


# =========================================================================
# 4. MONTE CARLO STOCHASTIC SIMULATION
# =========================================================================

def run_monte_carlo_simulation(
    base_revenue: float,
    mean_growth: float = 0.08,
    volatility: float = 0.05,
    operating_margin_mean: float = 0.156,
    operating_margin_std: float = 0.02,
    num_simulations: int = 5000,
    forecast_years: int = 3
) -> Dict[str, Any]:
    """
    Vectorized Monte Carlo simulation generating stochastic probability distributions
    for Revenue and Operating Income paths.
    """
    np.random.seed(42)  # Deterministic seed for reproducible testing

    # Simulate random growth trajectories: Geometric Brownian Motion variant
    # Shape: (num_simulations, forecast_years)
    growth_shocks = np.random.normal(loc=mean_growth, scale=volatility, size=(num_simulations, forecast_years))
    margin_shocks = np.random.normal(loc=operating_margin_mean, scale=operating_margin_std, size=(num_simulations, forecast_years))

    revenue_paths = np.zeros((num_simulations, forecast_years))
    op_income_paths = np.zeros((num_simulations, forecast_years))

    current_rev = np.full(num_simulations, base_revenue)

    for t in range(forecast_years):
        current_rev = current_rev * (1.0 + growth_shocks[:, t])
        revenue_paths[:, t] = current_rev
        op_income_paths[:, t] = current_rev * margin_shocks[:, t]

    final_rev = revenue_paths[:, -1]
    final_op_inc = op_income_paths[:, -1]

    # Percentiles
    percentiles = [10, 25, 50, 75, 90]
    rev_percentiles = {f"p{p}": round(float(np.percentile(final_rev, p)), 2) for p in percentiles}
    op_inc_percentiles = {f"p{p}": round(float(np.percentile(final_op_inc, p)), 2) for p in percentiles}

    # VaR (Value at Risk) at 95% confidence
    var_95_op_inc = round(float(np.percentile(final_op_inc, 5)), 2)

    return {
        "num_simulations": num_simulations,
        "forecast_horizon_years": forecast_years,
        "revenue_forecast_distribution": {
            "mean": round(float(np.mean(final_rev)), 2),
            "std_dev": round(float(np.std(final_rev)), 2),
            "percentiles": rev_percentiles
        },
        "operating_income_distribution": {
            "mean": round(float(np.mean(final_op_inc)), 2),
            "std_dev": round(float(np.std(final_op_inc)), 2),
            "percentiles": op_inc_percentiles,
            "value_at_risk_5pct": var_95_op_inc
        }
    }