"""
Forensic and Statistical Audit Analysis Engine
Vectorized calculations for Altman Z-Score, Beneish M-Score, Sloan Accruals,
DuPont ROE Decomposition, and Benford's Law Digital Analysis
"""

from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
from scipy import stats

from src.schemas.manifest import StatementType
from src.schemas.statements import StandardFinancialStatement
from src.analytics.core_analytics import _statement_to_dataframe, _get_metric

_g = _get_metric

# =========================================================================
# 1. ALTMAN Z-SCORE (Bankruptcy Prediction)
# =========================================================================

def compute_altman_z_score(
        bs_stmt: Optional[StandardFinancialStatement],
        is_stmt: Optional[StandardFinancialStatement],
) -> Dict[str, Any]:
    """
    Altman Z-Score model for Manufacturing/Corporate Non-Financials:
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 0.999*X5
    X1 = Working Capital / Total Assets
    X2 = Retained Earnings / Total Assets
    X3 = EBIT / Total Assets
    X4 = Total Equity / Total Liabilities
    X5 = Sales / Total Assets
    """
    bs = _statement_to_dataframe(bs_stmt)
    is_df = _statement_to_dataframe(is_stmt)

    tot_assets = _g(bs, "TotalAssets", default=1.0)
    ca = _g(bs, "TotalCurrentAssets")
    cl = _g(bs, "TotalCurrentLiabilities")
    re = _g(bs, "RetainedEarnings")
    equity = _g(bs, "TotalStockholdersEquity")
    tot_liab = _g(bs, "TotalLiabilities", default=1.0)

    ebit = _g(is_df, "OperatingIncome")
    sales = _g(is_df, "Revenue")

    x1 = (ca - cl) / tot_assets if tot_assets > 0 else 0.0
    x2 = re / tot_assets if tot_assets > 0 else 0.0
    x3 = ebit / tot_assets if tot_assets > 0 else 0.0
    x4 = equity / tot_liab if tot_liab > 0 else 0.0
    x5 = sales / tot_assets if tot_assets > 0 else 0.0

    weights = np.array([1.2, 1.4, 3.3, 0.6, 0.999])
    factors = np.array([x1, x2, x3, x4, x5])
    z_score = float(np.dot(weights, factors))

    if z_score > 2.99:
        zone = "SAFE ZONE (Low Distress Risk)"
        risk_level = "LOW"
    elif 1.81 <= z_score <= 2.99:
        zone = "GREY ZONE (Moderate Financial Stress)"
        risk_level = "MEDIUM"
    else:
        zone = "DISTRESS ZONE (High Bankruptcy Risk)"
        risk_level = "HIGH"

    return {
        "z_score": round(z_score, 2),
        "zone": zone,
        "risk_level": risk_level,
        "factors": {
            "X1_Working_Capital_to_Assets": round(x1, 3),
            "X2_Retained_Earnings_to_Assets": round(x2, 3),
            "X3_EBIT_to_Assets": round(x3, 3),
            "X4_Equity_to_Liabilities": round(x4, 3),
            "X5_Asset_Turnover": round(x5, 3),
        }
    }

# =========================================================================
# 2. BENEISH M-SCORE (Earnings Manipulation Detection)
# =========================================================================

def compute_beneish_m_score(
    bs_stmt: Optional[StandardFinancialStatement],
    is_stmt: Optional[StandardFinancialStatement],
    cfs_stmt: Optional[StandardFinancialStatement],
) -> Dict[str, Any]:

    """
    Beneish 8-Factor Earnings Manipulation model:
    M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.037*TATA + 0.0327*LVGI
    Benchmark: M > -1.78 flags a high probability of earnings manipulation.
    """

    bs = _statement_to_dataframe(bs_stmt)
    is_df = _statement_to_dataframe(is_stmt)
    cfs = _statement_to_dataframe(cfs_stmt)

    sales_cy = _g(is_df, "Revenue", col="cy_value", default=1.0)
    sales_py = _g(is_df, "Revenue", col="py_value", default=1.0)

    ar_cy = _g(bs, "AccountsReceivable", col="cy_value")
    ar_py = _g(bs, "AccountsReceivable", col="py_value", default=ar_cy or 1.0)

    cogs_cy = abs(_g(is_df, "CostOfGoodsSold", col="cy_value"))
    cogs_py = abs(_g(is_df, "CostOfGoodsSold", col="py_value", default=cogs_cy))

    ta_cy = _g(bs, "TotalAssets", col="cy_value", default=1.0)
    ta_py = _g(bs, "TotalAssets", col="py_value", default=ta_cy or 1.0)

    ca_cy = _g(bs, "TotalCurrentAssets", col="cy_value")
    ca_py = _g(bs, "TotalCurrentAssets", col="py_value", default=ca_cy)

    ppe_cy = _g(bs, "PropertyPlantAndEquipmentNet", col="cy_value")
    ppe_py = _g(bs, "PropertyPlantAndEquipmentNet", col="py_value", default=ppe_cy)

    depr_cy = _g(is_df, "DepreciationAndAmortizationExpense", col="cy_value", default=1.0)
    depr_py = _g(is_df, "DepreciationAndAmortizationExpense", col="py_value", default=depr_cy or 1.0)

    sga_cy = abs(_g(is_df, "SellingGeneralAndAdministrative", col="cy_value"))
    sga_py = abs(_g(is_df, "SellingGeneralAndAdministrative", col="py_value", default=sga_cy or 1.0))

    lt_debt_cy = _g(bs, "LongTermDebt", col="cy_value")
    lt_debt_py = _g(bs, "LongTermDebt", col="py_value", default=lt_debt_cy)

    cl_cy = _g(bs, "TotalCurrentLiabilities", col="cy_value")
    cl_py = _g(bs, "TotalCurrentLiabilities", col="py_value", default=cl_cy)

    net_inc = _g(is_df, "NetIncome", col="cy_value")
    cfo = _g(cfs, "OperatingCashFlow", col="cy_value")

    # 1. Days Sales in Receivables Index (DSRI)
    dsri = (ar_cy / sales_cy) / (ar_py / sales_py) if (ar_py / sales_py) > 0 else 1.0

    # 2. Gross Margin Index (GMI)
    gm_py = (sales_py - cogs_py) / sales_py if sales_py > 0 else 1.0
    gm_cy = (sales_cy - cogs_cy) / sales_cy if sales_cy > 0 else 1.0
    gmi = gm_py / gm_cy if gm_cy > 0 else 1.0

    # 3. Asset Quality Index (AQI)
    non_ca_ppe_cy = 1.0 - ((ca_cy + ppe_cy) / ta_cy) if ta_cy > 0 else 0.0
    non_ca_ppe_py = 1.0 - ((ca_py + ppe_py) / ta_py) if ta_py > 0 else 0.0
    aqi = non_ca_ppe_cy / non_ca_ppe_py if non_ca_ppe_py > 0 else 1.0

    # 4. Sales Growth Index (SGI)
    sgi = sales_cy / sales_py if sales_py > 0 else 1.0

    # 5. Depreciation Index (DEPI)
    dep_rate_py = depr_py / (ppe_py + depr_py) if (ppe_py + depr_py) > 0 else 1.0
    dep_rate_cy = depr_cy / (ppe_cy + depr_cy) if (ppe_cy + depr_cy) > 0 else 1.0
    depi = dep_rate_py / dep_rate_cy if dep_rate_cy > 0 else 1.0

    # 6. Sales, General & Administrative Expense Index (SGAI)
    sgai = (sga_cy / sales_cy) / (sga_py / sales_py) if (sga_py / sales_py) > 0 else 1.0

    # 7. Total Accruals to Total Assets (TATA)
    tata = (net_inc - cfo) / ta_cy if ta_cy > 0 else 0.0

    # 8. Leverage Index (LVGI)
    lev_cy = (lt_debt_cy + cl_cy) / ta_cy if ta_cy > 0 else 1.0
    lev_py = (lt_debt_py + cl_py) / ta_py if ta_py > 0 else 1.0
    lvgi = lev_cy / lev_py if lev_py > 0 else 1.0

    # 8 - variable linear regression
    m_score = float(
        -4.84 + 
        (0.920 * dsri) + 
        (0.528 * gmi) +
        (0.404 * aqi) + 
        (0.892 * sgi) + 
        (0.115 * depi) -
        (0.172 * sgai) + 
        (4.037 * tata) + 
        (0.0327 * lvgi)
    )

    is_flagged = m_score > -1.78

    return {
        "m_score": round(m_score, 2),
        "status": "FLAGGED (Potential Manipulation)" if is_flagged else "PASS (Unlikely Manipulation)",
        "threshold": -1.78,
        "indices": {
            "DSRI_Receivables_Index": round(dsri, 3),
            "GMI_Gross_Margin_Index": round(gmi, 3),
            "AQI_Asset_Quality_Index": round(aqi, 3),
            "SGI_Sales_Growth_Index": round(sgi, 3),
            "DEPI_Depreciation_Index": round(depi, 3),
            "SGAI_SGA_Index": round(sgai, 3),
            "TATA_Total_Accruals": round(tata, 3),
            "LVGI_Leverage_Index": round(lvgi, 3)
        }
    }

# =========================================================================
# 3. SLOAN ACCRUAL RATIO (Earnings Quality)
# =========================================================================

def compute_sloan_accrual_ratio(
    bs_stmt: Optional[StandardFinancialStatement],
    is_stmt: Optional[StandardFinancialStatement],
    cfs_stmt: Optional[StandardFinancialStatement],        
) -> Dict[str, Any]:
    """
    Sloan Accrual Ratio:
        Accrual Ratio = (Net Income - Operating Cash Flow - Investing Cash Flow) / Average Total Assets
        Safe Range: -10.0% to +10.0%. Values > 25.0% indicate low-quality non-cash earnings.
    """

    bs = _statement_to_dataframe(bs_stmt)
    is_df = _statement_to_dataframe(is_stmt)
    cfs = _statement_to_dataframe(cfs_stmt)

    ta_cy = _g(bs, "TotalAssets", col = "cy_value", default = 1.0)
    ta_py = _g(bs, "TotalAssets", col = "py_value", default = ta_cy)
    avg_assets = (ta_cy + ta_py) / 2.0

    net_inc = _g(is_df, "NetIncome", col = "cy_value")
    cfo = _g(cfs, "OperatingCashFlow", col = "cy_value")
    cfi = _g(cfs, "InvestingCashFlow", col = "cy_value")

    accruals = net_inc - (cfo + cfi)
    sloan_ratio = (accruals / avg_assets) * 100.0 if avg_assets > 0 else 0.0

    if -10.0 <= sloan_ratio <= 10.0:
        quality = "HIGH QUALITY (Cash-Back Earnings)"
    elif 10.0 < sloan_ratio <= 25.0:
        quality = "MODERATE QUALITY (Accepted Accruals)"
    else:
        quality = "LOW QUALITY (Excessive Accrual Overhang)"

    return {
        "sloan_accrual_ratio": f"{round(sloan_ratio, 2)}%",
        "earnings_quality": quality,
        "accrual_dollar_value": round(accruals, 2),
        "average_total_assets": round(avg_assets, 2)
    }

# =========================================================================
# 4. DUPONT 3-STAGE & 5-STAGE ROE DECOMPOSITION
# =========================================================================

def compute_dupont_roe_breakdown(
    bs_stmt: Optional[StandardFinancialStatement],
    is_stmt: Optional[StandardFinancialStatement],
) -> Dict[str, Any]:
    """
    3-stage DuPont: ROE = Net Margin * Asset Turnover * Equity Multiplier
    5-stage DuPont: ROE = Tax Burden * Interest Burden * Operating Margin * Asset Turnover * Equity Multiplier
    """

    bs = _statement_to_dataframe(bs_stmt)
    is_df = _statement_to_dataframe(is_stmt)

    sales = _g(is_df, "Revenue", default=1.0)
    ebit = _g(is_df, "OperatingIncome")
    ebt = _g(is_df, "EarningsBeforeTax", default=ebit)
    net_inc = _g(is_df, "NetIncome")

    tot_assets = _g(bs, "TotalAssets", default=1.0)
    equity = _g(bs, "TotalStockholdersEquity", default=1.0)

    # 3-Stage Factors
    net_margin = (net_inc / sales) if sales > 0 else 0.0
    asset_turnover = (sales / tot_assets) if tot_assets > 0 else 0.0
    equity_multiplier = (tot_assets / equity) if equity > 0 else 0.0
    roe_3stage = (net_margin * asset_turnover * equity_multiplier) * 100.0

    # 5-Stage Factors
    tax_burden = (net_inc / ebt) if ebt > 0 else 1.0
    interest_burden = (ebt / ebit) if ebit > 0 else 1.0
    op_margin = (ebit / sales) if sales > 0 else 0.0

    return {
        "roe_calculated": f"{round(roe_3stage, 2)}%",
        "3_stage_dupont": {
            "net_profit_margin": f"{round(net_margin * 100.0, 2)}%",
            "asset_turnover": round(asset_turnover, 2),
            "equity_multiplier": round(equity_multiplier, 2)
        },
        "5_stage_dupont": {
            "tax_burden": round(tax_burden, 3),
            "interest_burden": round(interest_burden, 3),
            "operating_margin": f"{round(op_margin * 100.0, 2)}%",
            "asset_turnover": round(asset_turnover, 2),
            "equity_multiplier": round(equity_multiplier, 2)
        }
    }

# =========================================================================
# 5. BENFORD'S LAW DIGITAL FREQUENCY ANALYSIS
# =========================================================================

def compute_benfords_law_analysis(
        statements: Dict[StatementType, StandardFinancialStatement]
) -> Dict[str, Any]:
    """
    Forensic Digital Frequency Engine:
    1. Chi-square Goodness of Fit
    2. Exact p-value determination
    3. Mean Absolute Deviation (MAD) conformity test
    4. Individual digit Z-score tests
    """

    numbers: List[float] = []

    for stmt in statements.values():
        if not stmt:
            continue
        for item in stmt.line_items:
            if item.cy_value and abs(float(item.cy_value)) >= 1.0:
                numbers.append(abs(float(item.cy_value)))
            if item.py_value and abs(float(item.py_value)) >= 1.0:
                numbers.append(abs(float(item.py_value)))

    if len(numbers) < 15:
        return {"status": "INSUFFICIENT SAMPLE SIZE", "sample_size": len(numbers)}

    # 1. Extract first significant non-zero digit
    first_digits = np.array([int(str(int(f))[0]) for f in numbers])
    first_digits = first_digits[(first_digits >= 1) & (first_digits <= 9)]
    n = len(first_digits)

    # 2. Theoretical Benford Probabilities
    digits = np.arange(1, 10)
    theoretical_probs = np.log10(1.0 + 1.0 / digits)
    expected_counts = theoretical_probs * n

    # 3. Observed Counts
    observed_counts = np.array([np.sum(first_digits == d) for d in digits])
    observed_probs = observed_counts / n

    # 4. SciPy Chi-Square Test
    chi2_stat, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)

    # 5. Nigrini Mean Absolute Deviation (MAD)
    # MAD = sum(|Observed_Prop - Expected_Prop|) / 9
    mad = float(np.sum(np.abs(observed_probs - theoretical_probs)) / 9.0)

    # Nigrini MAD Conformity Thresholds for First Digits
    if mad <= 0.006:
        mad_conformity = "CLOSE CONFORMITY"
    elif mad <= 0.012:
        mad_conformity = "ACCEPTABLE CONFORMITY"
    elif mad <= 0.015:
        mad_conformity = "MARGINALLY ACCEPTABLE CONFORMITY"
    else:
        mad_conformity = "NON_CONFORMANT (High Risk of Anomaly)"

    # 6. Digit-level Z-Scores: ( |p - P| - (1/(2N)) ) / sqrt( P*(1-P)/N )
    digit_z_scores = []
    for d, obs_p, exp_p in zip(digits, observed_probs, theoretical_probs):
        variance = (exp_p * (1.0 - exp_p)) / n
        std_err = np.sqrt(variance)
        # Continuity correction
        num = np.abs(obs_p - exp_p) - (1.0 / (2.0 * n))
        z = (num / std_err) if std_err > 0 else 0.0
        digit_z_scores.append(round(float(max(z, 0.0)), 2))

    dist_df = pd.DataFrame({
        "digit": digits,
        "observed_count": observed_counts,
        "observed_pct": (observed_probs * 100.0).round(2),
        "benford_expected_pct": (theoretical_probs * 100.0).round(2),
        "z_score": digit_z_scores,
        "is_digit_anomalous": [bool(x) for x in (np.array(digit_z_scores) > 1.96)]  # Significant at alpha=0.05
    })

    return {
        "overall_status": "PASS" if p_value > 0.05 and mad <= 0.015 else "FLAGGED",
        "chi_square_statistic": round(float(chi2_stat), 2),
        "p_value": round(float(p_value), 4),
        "mad_score": round(mad, 4),
        "mad_conformity_level": mad_conformity,
        "sample_size": int(n),
        "distribution_breakdown": dist_df.to_dict(orient="records")
    }

                        