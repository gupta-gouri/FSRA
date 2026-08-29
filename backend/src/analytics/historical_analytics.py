"""
Multi-Year Historical Trend Analysis Engine:
CAGR, Bps margin swings, Multi-year CCC trends, Asset Intensity, FCFF, and Cash Conversion Efficacy.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd


class HistoricalAnalyticsEngine:
    def __init__(self, historical_statements: pd.DataFrame):
        """
        historical_statements DataFrame expected structure:
        Indexed or containing 'fiscal_year' (sorted ascending), with columns:
          - revenue
          - cogs
          - gross_profit
          - opex
          - operating_income (ebit)
          - depreciation_amortization
          - tax_expense
          - net_income
          - cash
          - accounts_receivable
          - inventory
          - accounts_payable
          - ppe_net
          - total_assets
          - total_equity
          - operating_cash_flow
          - capex
        """
        self.df = historical_statements.sort_values("fiscal_year").reset_index(drop=True)
        self.periods = len(self.df)

    # =========================================================================
    # 1. COMPOUND ANNUAL GROWTH RATE (CAGR)
    # =========================================================================
    def calculate_cagr(self, metrics: Optional[List[str]] = None) -> Dict[str, float]:
        """
        CAGR = (End Value / Beginning Value) ** (1 / n) - 1
        Calculates CAGR across top-line and earnings metrics.
        """
        if self.periods < 2:
            return {}

        if metrics is None:
            metrics = ["revenue", "gross_profit", "operating_income", "net_income", "total_assets"]

        n_years = self.periods - 1
        cagr_results = {}

        for col in metrics:
            if col in self.df.columns:
                beg_val = float(self.df[col].iloc[0])
                end_val = float(self.df[col].iloc[-1])
                if beg_val > 0 and end_val > 0:
                    cagr = ((end_val / beg_val) ** (1.0 / n_years)) - 1.0
                    cagr_results[f"{col}_cagr"] = round(cagr * 100.0, 2)
                else:
                    cagr_results[f"{col}_cagr"] = np.nan

        return cagr_results

    # =========================================================================
    # 2. BASIS POINTS (BPS) MARGIN SWINGS
    # =========================================================================
    def calculate_bps_margin_swings(self) -> pd.DataFrame:
        """
        Calculates YoY swings in Basis Points (1% = 100 bps) for:
          - Gross Margin
          - Operating Margin (EBIT Margin)
          - Net Profit Margin
        """
        df = self.df.copy()
        rev = df["revenue"]

        # Margins in %
        df["gross_margin_pct"] = (df["gross_profit"] / rev) * 100.0
        df["operating_margin_pct"] = (df["operating_income"] / rev) * 100.0
        df["net_margin_pct"] = (df["net_income"] / rev) * 100.0

        # Basis point shifts (YoY diff * 100)
        df["gross_margin_bps_swing"] = (df["gross_margin_pct"].diff() * 100.0).round(1)
        df["operating_margin_bps_swing"] = (df["operating_margin_pct"].diff() * 100.0).round(1)
        df["net_margin_bps_swing"] = (df["net_margin_pct"].diff() * 100.0).round(1)

        cols = [
            "fiscal_year",
            "gross_margin_pct", "gross_margin_bps_swing",
            "operating_margin_pct", "operating_margin_bps_swing",
            "net_margin_pct", "net_margin_bps_swing"
        ]
        return df[cols].round(2)

    # =========================================================================
    # 3. MULTI-YEAR CCC TRENDS (DIO, DSO, DPO)
    # =========================================================================
    def calculate_multi_year_ccc(self) -> pd.DataFrame:
        """Tracks working capital efficiency over time: DIO, DSO, DPO, and net CCC days."""
        df = self.df.copy()
        cogs = df["cogs"].abs()
        rev = df["revenue"]

        df["dio_days"] = np.where(cogs > 0, (df["inventory"] / cogs) * 365.0, 0.0)
        df["dso_days"] = np.where(rev > 0, (df["accounts_receivable"] / rev) * 365.0, 0.0)
        df["dpo_days"] = np.where(cogs > 0, (df["accounts_payable"] / cogs) * 365.0, 0.0)
        df["ccc_net_days"] = df["dio_days"] + df["dso_days"] - df["dpo_days"]

        cols = ["fiscal_year", "dio_days", "dso_days", "dpo_days", "ccc_net_days"]
        return df[cols].round(1)

    # =========================================================================
    # 4. ASSET INTENSITY & TURNOVER TRENDS
    # =========================================================================
    def calculate_asset_intensity(self) -> pd.DataFrame:
        """
        Calculates capital intensity and asset efficiency metrics:
          - Fixed Asset Turnover (FAT) = Revenue / Net PP&E
          - Total Asset Turnover (TAT) = Revenue / Total Assets
          - Capital Intensity Ratio = Total Assets / Revenue
        """
        df = self.df.copy()
        rev = df["revenue"]

        df["fixed_asset_turnover"] = np.where(df["ppe_net"] > 0, rev / df["ppe_net"], 0.0)
        df["total_asset_turnover"] = np.where(df["total_assets"] > 0, rev / df["total_assets"], 0.0)
        df["capital_intensity_ratio"] = np.where(rev > 0, df["total_assets"] / rev, 0.0)

        cols = ["fiscal_year", "fixed_asset_turnover", "total_asset_turnover", "capital_intensity_ratio"]
        return df[cols].round(2)

    # =========================================================================
    # 5. HISTORICAL FREE CASH FLOW TO FIRM (FCFF)
    # =========================================================================
    def calculate_historical_fcff(self, tax_rate: float = 0.25) -> pd.DataFrame:
        """
        FCFF = EBIT * (1 - Tax Rate) + D&A - CapEx - Delta(Non-Cash Working Capital)
        """
        df = self.df.copy()
        ebit = df["operating_income"]
        da = df["depreciation_amortization"]
        capex = df["capex"].abs()

        nwc = (df["accounts_receivable"] + df["inventory"]) - df["accounts_payable"]
        delta_nwc = nwc.diff().fillna(0.0)

        nopat = ebit * (1.0 - tax_rate)
        df["nopat"] = nopat
        df["delta_nwc"] = delta_nwc
        df["fcff"] = nopat + da - capex - delta_nwc

        cols = ["fiscal_year", "operating_income", "nopat", "depreciation_amortization", "capex", "delta_nwc", "fcff"]
        return df[cols].round(2)

    # =========================================================================
    # 6. CASH CONVERSION EFFICACY (FCF / EBITDA)
    # =========================================================================
    def calculate_cash_conversion_efficacy(self) -> pd.DataFrame:
        """
        Cash Conversion Efficacy = Free Cash Flow / EBITDA
        Measures the percentage of operating cash earnings converted directly into free cash.
        """
        df = self.df.copy()
        ebitda = df["operating_income"] + df["depreciation_amortization"]
        fcf = df["operating_cash_flow"] - df["capex"].abs()

        df["ebitda"] = ebitda
        df["free_cash_flow"] = fcf
        df["fcf_to_ebitda_efficacy_pct"] = np.where(ebitda > 0, (fcf / ebitda) * 100.0, 0.0)

        cols = ["fiscal_year", "ebitda", "operating_cash_flow", "capex", "free_cash_flow", "fcf_to_ebitda_efficacy_pct"]
        return df[cols].round(2)

    # =========================================================================
    # CONSOLIDATED HISTORICAL BASELINE REPORT
    # =========================================================================
    def generate_full_historical_report(self) -> Dict[str, Any]:
        return {
            "cagr_metrics": self.calculate_cagr(),
            "margin_bps_swings": self.calculate_bps_margin_swings().to_dict(orient="records"),
            "working_capital_ccc_trends": self.calculate_multi_year_ccc().to_dict(orient="records"),
            "asset_intensity_trends": self.calculate_asset_intensity().to_dict(orient="records"),
            "fcff_historical": self.calculate_historical_fcff().to_dict(orient="records"),
            "cash_conversion_efficacy": self.calculate_cash_conversion_efficacy().to_dict(orient="records")
        }