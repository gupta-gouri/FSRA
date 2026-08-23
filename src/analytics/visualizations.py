"""
analytics/visualizations.py
Generates Static (Matplotlib/Seaborn) and Interactive (Plotly/Recharts JSON) Visualizations.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px


# =========================================================================
# 1. CASH FLOW WATERFALL BRIDGE
# =========================================================================

def plot_cash_flow_waterfall(
    beg_cash: float,
    ocf: float,
    icf: float,
    fcf: float,
    end_cash: float,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Generates a Cash Flow Waterfall Bridge (Beginning Cash -> OCF -> ICF -> FCF -> Ending Cash)."""
    measures = ["absolute", "relative", "relative", "relative", "total"]
    x_labels = ["Beginning Cash", "Operating CF", "Investing CF", "Financing CF", "Ending Cash"]
    y_vals = [beg_cash, ocf, icf, fcf, end_cash]

    # Interactive Plotly Object
    fig = go.Figure(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=measures,
        x=x_labels,
        textposition="outside",
        text=[f"{v:+,.1f}" if m == "relative" else f"{v:,.1f}" for v, m in zip(y_vals, measures)],
        y=y_vals,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#EF553B"}},
        increasing={"marker": {"color": "#00CC96"}},
        totals={"marker": {"color": "#636EFA"}}
    ))
    fig.update_layout(title="Cash Flow Waterfall Bridge", waterfallgap=0.3)

    if output_path:
        fig.write_image(output_path)

    return fig.to_dict()


# =========================================================================
# 2. CCC BREAKDOWN (DIO, DSO, DPO)
# =========================================================================

def plot_ccc_breakdown(dio: float, dso: float, dpo: float) -> Dict[str, Any]:
    """Visualizes the Cash Conversion Cycle components: CCC = DIO + DSO - DPO."""
    ccc = dio + dso - dpo
    fig = go.Figure()
    fig.add_trace(go.Bar(name="DIO (Inventory)", x=["Working Capital Cycle"], y=[dio], marker_color="#FFA15A"))
    fig.add_trace(go.Bar(name="DSO (Receivables)", x=["Working Capital Cycle"], y=[dso], marker_color="#19D3F3"))
    fig.add_trace(go.Bar(name="Less: DPO (Payables)", x=["Working Capital Cycle"], y=[-dpo], marker_color="#AB63FA"))
    fig.add_trace(go.Scatter(name="Net CCC Days", x=["Working Capital Cycle"], y=[ccc], mode="text+markers", text=[f"CCC: {ccc:.1f} Days"], textposition="top center", marker=dict(size=12, color="black")))
    fig.update_layout(barmode="relative", title=f"Cash Conversion Cycle Breakdown: {ccc:.1f} Net Days")
    return fig.to_dict()


# =========================================================================
# 3. DYNAMIC CASH RUNWAY VELOCITY GAUGE
# =========================================================================

def plot_cash_runway_gauge(cash_balance: float, monthly_burn: float) -> Dict[str, Any]:
    """Generates a speedometer gauge indicating months of cash runway remaining."""
    runway_months = (cash_balance / monthly_burn) if monthly_burn > 0 else 36.0
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(runway_months, 1),
        title={"text": "Cash Runway Velocity (Months)"},
        gauge={
            "axis": {"range": [0, 24]},
            "bar": {"color": "#2CA02C" if runway_months >= 12 else ("#FF7F0E" if runway_months >= 6 else "#D62728")},
            "steps": [
                {"range": [0, 6], "color": "#FFCCCC"},
                {"range": [6, 12], "color": "#FFF2CC"},
                {"range": [12, 24], "color": "#D9EAD3"}
            ],
            "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 6.0}
        }
    ))
    return fig.to_dict()

# =========================================================================
# 4. HORIZONTAL YoY VARIANCE TORNADO CHART
# =========================================================================

def plot_yoy_tornado_chart(yoy_df: pd.DataFrame) -> Dict[str, Any]:
    """Generates a horizontal tornado bar chart of YoY percentage swings."""
    if yoy_df.empty or "pct_change" not in yoy_df.columns or "line_item" not in yoy_df.columns:
        return go.Figure().to_dict()

    plot_df = yoy_df.dropna(subset=["pct_change"]).sort_values("pct_change", ascending=True)
    colors = ["#EF553B" if v < 0 else "#00CC96" for v in plot_df["pct_change"]]

    fig = go.Figure(go.Bar(
        x=plot_df["pct_change"],
        y=plot_df["line_item"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}%" for v in plot_df["pct_change"]],
        textposition="outside"
    ))
    fig.update_layout(title="YoY Line Item Percentage Variance (Tornado)", xaxis_title="% Change", yaxis_title="")
    return fig.to_dict()


# =========================================================================
# 5. COMMON-SIZE 100% STACKED BAR CHART
# =========================================================================

def plot_common_size_stacked(common_bs_df: pd.DataFrame) -> Dict[str, Any]:
    """Generates a 100% stacked vertical structure chart for Balance Sheet composition."""
    if common_bs_df.empty:
        return go.Figure().to_dict()

    col_name = "common_size_bs_pct" if "common_size_bs_pct" in common_bs_df.columns else (
        "percent_of_total_assets" if "percent_of_total_assets" in common_bs_df.columns else common_bs_df.columns[-1]
    )

    fig = px.bar(
        common_bs_df,
        x=["Composition"] * len(common_bs_df),
        y=col_name,
        color="line_item" if "line_item" in common_bs_df.columns else None,
        title="Balance Sheet Vertical Composition (% of Total Assets)",
        text=col_name
    )
    fig.update_layout(barmode="stack", yaxis=dict(title="% of Total Assets", range=[0, 100]))
    return fig.to_dict()


# =========================================================================
# 6. BUDGET VS ACTUAL (BVA) ATTAINMENT MATRIX
# =========================================================================

def plot_bva_matrix(actuals: Dict[str, float], budget: Dict[str, float]) -> Dict[str, Any]:
    """Visualizes Budget vs Actual performance and % attainment."""
    categories = list(actuals.keys())
    act_vals = [actuals[k] for k in categories]
    bud_vals = [budget.get(k, act_vals[idx]) for idx, k in enumerate(categories)]
    attainment = [(a / b * 100.0) if b > 0 else 100.0 for a, b in zip(act_vals, bud_vals)]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Budget Target", x=categories, y=bud_vals, marker_color="#B0BEC5"))
    fig.add_trace(go.Bar(name="Actual Result", x=categories, y=act_vals, marker_color="#1E88E5", text=[f"{att:.1f}% Attained" for att in attainment], textposition="outside"))
    fig.update_layout(barmode="group", title="Budget vs. Actual (BVA) Attainment Matrix")
    return fig.to_dict()


# =========================================================================
# 7. BENFORD'S LAW DIGITAL DISTRIBUTION CURVE
# =========================================================================

def plot_benfords_law_curve(benford_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Plots empirical leading-digit distribution against the theoretical log10 Benford curve."""
    dist = benford_dict.get("distribution_breakdown", benford_dict.get("distribution_table", []))
    df = pd.DataFrame(dist)
    if df.empty:
        return {}

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["digit"], y=df["observed_pct"], name="Observed Distribution", marker_color="#42A5F5"))
    fig.add_trace(go.Scatter(x=df["digit"], y=df["benford_expected_pct"], name="Theoretical Benford Curve", mode="lines+markers", line=dict(color="#E53935", width=3)))
    fig.update_layout(
        title=f"Benford's Law First-Digit Analysis (Status: {benford_dict.get('overall_status', benford_dict.get('status'))})",
        xaxis=dict(title="First Significant Digit (1-9)", tickmode="linear"),
        yaxis=dict(title="Probability (%)")
    )
    return fig.to_dict()


# =========================================================================
# 8. ALTMAN Z & BENEISH M DUAL-AXIS RISK BANDS
# =========================================================================

def plot_altman_beneish_risk_bands(z_score: float, m_score: float) -> Dict[str, Any]:
    """Plots Altman Z-Score and Beneish M-Score against their critical threshold risk bands."""
    fig = go.Figure()
    # Altman Z Bar
    fig.add_trace(go.Bar(name="Altman Z-Score", x=["Altman Z (Distress)"], y=[z_score], marker_color="#4CAF50" if z_score > 2.99 else ("#FF9800" if z_score >= 1.81 else "#F44336")))
    # Beneish M Bar
    fig.add_trace(go.Bar(name="Beneish M-Score", x=["Beneish M (Manipulation)"], y=[m_score], marker_color="#F44336" if m_score > -1.78 else "#4CAF50"))
    # Add Threshold Reference Lines
    fig.add_hline(y=1.81, line_dash="dash", line_color="orange", annotation_text="Altman Distress Cutoff (1.81)")
    fig.add_hline(y=-1.78, line_dash="dot", line_color="red", annotation_text="Beneish Manipulation Cutoff (-1.78)")
    fig.update_layout(title="Altman Z vs. Beneish M Forensic Risk Matrix")
    return fig.to_dict()


# =========================================================================
# 9. OPERATIONAL DISCONNECT LINE PLOTS
# =========================================================================

def plot_operational_disconnects(rel_df: pd.DataFrame) -> Dict[str, Any]:
    """Generates audit status bars across all 6 structural relationship disconnect rules."""
    if rel_df.empty or "rule_id" not in rel_df.columns or "status" not in rel_df.columns:
        return go.Figure().to_dict()

    colors = ["#4CAF50" if s == "PASS" else "#F44336" for s in rel_df["status"]]
    fig = go.Figure(go.Bar(
        x=rel_df["rule_id"],
        y=[1] * len(rel_df),
        marker_color=colors,
        text=[f"{r}: {s}" for r, s in zip(rel_df["rule_id"], rel_df["status"])],
        textposition="inside"
    ))
    fig.update_layout(title="Universal Relationship Disconnects (Pass / Flagged Summary)", yaxis=dict(visible=False))
    return fig.to_dict()


# =========================================================================
# 10. DUPONT 5-STEP DECOMPOSITION SUNBURST / TREE
# =========================================================================

def plot_dupont_sunburst(dupont_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a hierarchical tree/sunburst visualization of the 5-step DuPont ROE model."""
    d5 = dupont_dict.get("5_stage_dupont", {})
    roe_val = dupont_dict.get("roe_calculated", "0.0%")

    labels = ["ROE", "Operating Efficiency", "Asset Use Efficiency", "Financial Leverage", "Tax Burden", "Interest Burden", "Operating Margin", "Asset Turnover", "Equity Multiplier"]
    parents = ["", "ROE", "ROE", "ROE", "Operating Efficiency", "Operating Efficiency", "Operating Efficiency", "Asset Use Efficiency", "Financial Leverage"]
    values = [100, 40, 30, 30, 15, 15, 10, 30, 30]

    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        textinfo="label+percent parent"
    ))
    fig.update_layout(title=f"DuPont 5-Stage ROE Structural Decomposition (Total ROE: {roe_val})")
    return fig.to_dict()
