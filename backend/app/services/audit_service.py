from pathlib import Path
import pandas as pd
from typing import List, Union, Dict, Any, Optional

from src.ingestion.orchestrator import ingest_sources
from src.schemas.manifest import IngestionManifest, StatementType
from src.extraction.extractor import extract_statements_from_manifest
from src.schemas.statements import StandardFinancialStatement
from src.verification.orchestrator import MathEngine
from src.analytics.core_analytics import (
    calculate_horizontal_vertical_analysis,
    calculate_financial_ratios,
    evaluate_relationship_disconnects
)
from src.analytics.historical_analytics import HistoricalAnalyticsEngine
from src.analytics.forensics import (
    compute_altman_z_score,
    compute_beneish_m_score,
    compute_sloan_accrual_ratio,
    compute_dupont_roe_breakdown,
    compute_benfords_law_analysis,
)
from src.analytics.forecast import (
    forecast_driver_based_3_statement, 
    forecast_holt_winters,
    forecast_arima_sarimax, 
    run_monte_carlo_simulation
)
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
    plot_dupont_sunburst
)
from src.reporting.report_orchestrator import generate_full_audit_package
from src.reporting.workpaper_exporter import build_audit_workbook, build_audit_pdf
from app.core.supabase import supabase

class AuditService:
    @staticmethod
    def stage1_ingest(
        file_paths: List[Union[str, Path]], 
        resolve_conflicts: bool = False, 
        interactive: bool = False
    ) -> IngestionManifest:
        """Stage 1: Parses raw Excel and PDF files into a structured IngestionManifest."""
        return ingest_sources(
            file_paths = file_paths,
            resolve_conflicts = resolve_conflicts,
            interactive = interactive
        )

    @staticmethod
    def stage2_extract(
        manifest: IngestionManifest,
        apply_scale: bool = True
    ) -> Dict[str, Any]:
        """Stage 2: Extracts standardized financial statements (BS, IS, CF, TB) from the IngestionManifest, resolving scale factors and mapping taxonomy."""
        return extract_statements_from_manifest(
            manifest = manifest,
            apply_scale = apply_scale
        )

    @staticmethod
    def stage3_verify(
        statements: Dict[StatementType, StandardFinancialStatement],
        manifest: IngestionManifest
    ) -> Dict[str, Any]:
        """Stage 3: All the mathematical verifications are done here."""
        engine = MathEngine(
            statements = statements,
            manifest = manifest
        )
        return engine.generate_structured_audit_report()
        
    @staticmethod
    def stage4_analytics(
        statements: Dict[StatementType, StandardFinancialStatement],
        historical_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Stage 4: Executes core Financial analytics, Forensics risk scoring"""
        analysis_df = calculate_horizontal_vertical_analysis(statements)
        ratios = calculate_financial_ratios(statements)
        disconnects = evaluate_relationship_disconnects(statements)

        altman_z = compute_altman_z_score(statements)
        beneish_m = compute_beneish_m_score(statements)
        sloan_accrual = compute_sloan_accrual_ratio(statements)
        dupont_roe = compute_dupont_roe_breakdown(statements)
        benford_law = compute_benfords_law_analysis(statements)

        historical_report = None
        if historical_df is not None and not historical_df.empty:
            hist_engine = HistoricalAnalyticsEngine(historical_df)
            historical_report = hist_engine.generate_full_historical_report()

        return {
            "ratios": ratios,
            "disconnects": disconnects,
            "analysis_table": analysis_df.to_dict(orient="records") if not analysis_df.empty else [],
            "forensics": {
                "altman_z_score": altman_z,
                "beneish_m_score": beneish_m,
                "sloan_accrual_ratio": sloan_accrual,
                "dupont_roe_breakdown": dupont_roe,
                "benford_law_analysis": benford_law
            },
            "historical_trends": historical_report
        }

    @staticmethod
    def stage5_forecasting(
        base_year_data: Dict[str, float],
        series_data: Optional[List[float]] = None,
        forecast_years: int = 3,
        num_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Stage 5: Driver-based 3-statement forecasting, time series 
        (Holt-Winters / ARIMA), and Monte Carlo simulation.
        """
        forecast_results: Dict[str, Any] = {}

        # 1. Driver-Based 3-Statement Model
        driver_model = forecast_driver_based_3_statement(
            base_year_data=base_year_data,
            forecast_years=forecast_years
        )
        forecast_results["driver_based_model"] = driver_model.to_dict(orient="records")

        # 2. Time-Series Forecasting (Holt-Winters & ARIMA)
        if series_data and len(series_data) >= 4:
            hw_model = forecast_holt_winters(series_data, steps=forecast_years)
            arima_model = forecast_arima_sarimax(series_data, steps=forecast_years)
            forecast_results["holt_winters"] = hw_model
            forecast_results["arima_sarimax"] = arima_model

        # 3. Monte Carlo Stochastic Simulation (1,000 runs)
        rev_base = base_year_data.get("revenue", 1000000.0)
        monte_carlo = run_monte_carlo_simulation(
            base_val=rev_base,
            mean_growth=0.08,
            volatility=0.15,
            years=forecast_years,
            num_simulations=num_simulations
        )
        forecast_results["monte_carlo_simulation"] = monte_carlo

        return forecast_results

    @staticmethod
    def stage6_visualizations(
        analytics_data: Dict[str, Any],
        cash_flow_data: Optional[Dict[str, float]] = None,
        operational_metrics: Optional[Dict[str, float]] = None,
        budget_vs_actual: Optional[Dict[str, Dict[str, float]]] = None,
        yoy_df: Optional[pd.DataFrame] = None,
        common_bs_df: Optional[pd.DataFrame] = None,
        rel_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Stage 6: Generates all 10 interactive Plotly & static visualization figure objects.
        """
        charts: Dict[str, Any] = {}

        # 1. Cash Flow Waterfall Bridge
        if cash_flow_data:
            charts["cash_flow_waterfall"] = plot_cash_flow_waterfall(
                beg_cash=cash_flow_data.get("beg_cash", 0.0),
                ocf=cash_flow_data.get("ocf", 0.0),
                icf=cash_flow_data.get("icf", 0.0),
                fcf=cash_flow_data.get("fcf", 0.0),
                end_cash=cash_flow_data.get("end_cash", 0.0)
            )

        # 2. Operational & Liquidity Gauges
        if operational_metrics:
            charts["ccc_breakdown"] = plot_ccc_breakdown(
                dio=operational_metrics.get("dio", 0.0),
                dso=operational_metrics.get("dso", 0.0),
                dpo=operational_metrics.get("dpo", 0.0)
            )
            charts["cash_runway_gauge"] = plot_cash_runway_gauge(
                cash_balance=operational_metrics.get("cash_balance", 0.0),
                monthly_burn=operational_metrics.get("monthly_burn", 1.0)
            )

        # 3. YoY Tornado Chart
        if yoy_df is not None and not yoy_df.empty:
            charts["yoy_tornado_chart"] = plot_yoy_tornado_chart(yoy_df)

        # 4. Common-Size Stacked Bar Chart
        if common_bs_df is not None and not common_bs_df.empty:
            charts["common_size_stacked"] = plot_common_size_stacked(common_bs_df)

        # 5. Budget vs. Actual Matrix
        if budget_vs_actual:
            charts["bva_matrix"] = plot_bva_matrix(
                actuals=budget_vs_actual.get("actuals", {}),
                budget=budget_vs_actual.get("budget", {})
            )

        # 6. Operational Disconnects Matrix
        if rel_df is not None and not rel_df.empty:
            charts["operational_disconnects"] = plot_operational_disconnects(rel_df)

        # 7. Forensic Risk & Statistical Visualizations
        if "forensics" in analytics_data:
            forensics = analytics_data["forensics"]
            z_score = forensics.get("altman_z_score", {}).get("z_score", 0.0)
            m_score = forensics.get("beneish_m_score", {}).get("m_score", 0.0)

            charts["altman_beneish_risk_bands"] = plot_altman_beneish_risk_bands(
                z_score=z_score,
                m_score=m_score
            )
            charts["dupont_sunburst"] = plot_dupont_sunburst(
                dupont_dict=forensics.get("dupont_roe_breakdown", {})
            )
            charts["benfords_law_curve"] = plot_benfords_law_curve(
                benford_dict=forensics.get("benford_law_analysis", {})
            )

        return charts

    @staticmethod
    def stage7_report(
        statements: Dict[StatementType, StandardFinancialStatement],
        manifest: IngestionManifest,
        audit_report: Optional[Dict[str, Any]] = None,
        output_dir: Path = Path("audit_output")
    ) -> Dict[str, Any]:
        """
        Stage 7: Compiles full audit package and exports PDF Audit Report & XLSX Workpapers.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        # 1. Full Package Generation
        package_paths = generate_full_audit_package(
            statements=statements,
            manifest=manifest,
            output_dir=output_dir
        )
        # 2. Standalone Workpaper & Report Builds
        xlsx_path = package_paths.get("xlsx_path")
        pdf_path = package_paths.get("pdf_path")
        if audit_report:
            xlsx_target = output_dir / "WP-514_Audit_Workbook.xlsx"
            pdf_target = output_dir / "WP-514_Audit_Report.pdf"
            xlsx_path = str(build_audit_workbook(audit_report, xlsx_target))
            pdf_path = str(build_audit_pdf(audit_report, pdf_target))
        return {
            "package_paths": package_paths,
            "excel_workbook": xlsx_path,
            "pdf_report": pdf_path
        }

    @classmethod
    def run_full_audit_pipeline(
        cls,
        file_paths: List[Union[str, Path]],
        output_dir: Path = Path("audit_output"),
        apply_scale: bool = True
    ) -> Dict[str, Any]:
        """
        Runs the complete 7-stage FSRA audit, forecasting, visualization, 
        and reporting pipeline end-to-end.
        """
        # -------------------------------------------------------------
        # Stage 1: Ingestion & Statement Classification
        # -------------------------------------------------------------
        manifest = cls.stage1_ingest(file_paths)

        # -------------------------------------------------------------
        # Stage 2: Financial Statement & Trial Balance Extraction
        # -------------------------------------------------------------
        extracted_data = cls.stage2_extract(manifest, apply_scale=apply_scale)

        statements: Dict[StatementType, StandardFinancialStatement] = {
            StatementType(k): v
            for k, v in extracted_data.items()
            if k != "TRIAL_BALANCE" and isinstance(v, StandardFinancialStatement)
        }

        # -------------------------------------------------------------
        # Stage 3: Deterministic Math Verification & Guardrails
        # -------------------------------------------------------------
        verification = cls.stage3_verify(statements, manifest)

        # -------------------------------------------------------------
        # Stage 4: Financial Analytics & Forensic Models
        # -------------------------------------------------------------
        analytics = cls.stage4_analytics(statements)

        # -------------------------------------------------------------
        # Stage 5: Predictive & 3-Statement Forecasting
        # -------------------------------------------------------------
        base_year_data: Dict[str, float] = {}
        if StatementType.INCOME_STATEMENT in statements:
            is_stmt = statements[StatementType.INCOME_STATEMENT]
            base_year_data["revenue"] = float(is_stmt.key_map_cy.get("Revenue") or 1000000.0)
            base_year_data["net_income"] = float(is_stmt.key_map_cy.get("NetIncome") or 100000.0)
            base_year_data["operating_income"] = float(is_stmt.key_map_cy.get("OperatingIncome") or 150000.0)

        forecasting = cls.stage5_forecasting(base_year_data=base_year_data) if base_year_data else {}

        # -------------------------------------------------------------
        # Stage 6: Interactive & Static Visualizations (10 Figure Objects)
        # -------------------------------------------------------------
        visualizations = cls.stage6_visualizations(analytics_data=analytics)

        # -------------------------------------------------------------
        # Stage 7: PDF Report & Excel Deliverables Export
        # -------------------------------------------------------------
        deliverables = cls.stage7_report(
            statements=statements,
            manifest=manifest,
            audit_report=verification,
            output_dir=output_dir
        )

        return {
            "metadata": manifest.metadata.model_dump(),
            "audit_status": verification.get("audit_status", "PENDING"),
            "verification": verification,
            "analytics": analytics,
            "forecasting": forecasting,
            "visualizations": list(visualizations.keys()),
            "deliverables": deliverables
        }