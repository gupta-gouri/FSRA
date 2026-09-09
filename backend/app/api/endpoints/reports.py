import os
import tempfile
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from app.core.supabase import supabase

router = APIRouter()

@router.get("/download/{project_id}", status_code=status.HTTP_200_OK)
async def download_audit_deliverable(
    project_id: UUID,
    report_type: str = Query("pdf", regex="^(pdf|xlsx)$", description="Deliverable format: 'pdf' or 'xlsx'")
):
    """
    Locates and streams the compiled audit report (PDF) or 
    structured workpaper workbook (XLSX) for a specific project.
    """
    # 1. Verify project audit execution exists in DB
    res = (
        supabase.table("audit_results")
        .select("id, created_at")
        .eq("project_id", str(project_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No audit results found for this project. Please execute the pipeline first."
        )

    # 2. Resolve file name and search expected output directories
    filename = "WP-514_Audit_Report.pdf" if report_type == "pdf" else "WP-514_Audit_Workbook.xlsx"
    
    possible_paths = [
        Path("audit_output") / filename,
        Path(f"audit_output_{project_id}") / filename,
        Path(tempfile.gettempdir()) / f"audit_output_{project_id}" / filename,
        Path(tempfile.gettempdir()) / filename
    ]

    target_file = None
    for path in possible_paths:
        if path.exists():
            target_file = path
            break

    if not target_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The requested {report_type.upper()} deliverable file could not be located on server storage."
        )

    # 3. Set correct MIME type and stream response
    media_type = (
        "application/pdf" 
        if report_type == "pdf" 
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return FileResponse(
        path=target_file,
        media_type=media_type,
        filename=filename
    )