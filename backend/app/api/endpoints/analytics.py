from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.core.supabase import supabase

router = APIRouter()

@router.get("/{project_id}/summary", status_code=status.HTTP_200_OK)
async def get_full_analytics_summary(project_id: UUID):
    """
    Returns complete financial analytics, forensics, and forecasts stored for the project.
    """
    res = (
        supabase.table("audit_results")
        .select("id, project_id, analytics_data, forensics_data, forecast_data, created_at")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analytics data not found. Ensure pipeline execution has completed."
        )

    record = res.data[0]
    return {
        "project_id": project_id,
        "run_id": record["id"],
        "calculated_at": record["created_at"],
        "analytics": record.get("analytics_data") or {},
        "forensics": record.get("forensics_data") or {},
        "forecasting": record.get("forecast_data") or {}
    }

@router.get("/{project_id}/forensics", status_code=status.HTTP_200_OK)
async def get_forensics_breakdown(project_id: UUID):
    """
    Targeted endpoint for forensic risk metrics: Altman Z-Score, Beneish M-Score,
    Sloan Accruals, DuPont breakdown, and Benford's Law.
    """
    res = (
        supabase.table("audit_results")
        .select("id, forensics_data, created_at")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Forensics results not found for this project."
        )

    return {
        "project_id": project_id,
        "forensics": res.data[0].get("forensics_data") or {}
    }

@router.get("/{project_id}/forecasts", status_code=status.HTTP_200_OK)
async def get_forecast_models(project_id: UUID):
    """
    Targeted endpoint for 3-statement driver forecasts, time series, and Monte Carlo runs.
    """
    res = (
        supabase.table("audit_results")
        .select("id, forecast_data, created_at")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Forecast models not found for this project."
        )

    return {
        "project_id": project_id,
        "forecasting": res.data[0].get("forecast_data") or {}
    }