import tempfile
import os
from pathlib import Path
from typing import List, Optional, Any
from uuid import UUID
from decimal import Decimal
import numpy as np
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from app.core.supabase import supabase
from app.services.service import AuditService

router = APIRouter()
STORAGE_BUCKET = "audit-files"
SIGNED_URL_EXPIRY = 86400  # 24 hours link

import math

def sanitize_for_json(obj: Any) -> Any:
    """Recursively converts Decimals, numpy types, NaNs, and Infs into JSON-compliant primitives."""
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, tuple):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, Decimal):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    elif isinstance(obj, np.ndarray):
        return [sanitize_for_json(i) for i in obj.tolist()]
    elif isinstance(obj, set):
        return list(obj)
    return obj

def _generate_signed_url(storage_path: str) -> Optional[str]:
    """Generates a temporary signed download URL for files stored in Supabase private bucket."""
    try:
        res = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(path=storage_path, expires_in=SIGNED_URL_EXPIRY)
        return res.get("signedURL") or res.get("signedUrl")
    except Exception:
        return None

def run_audit_pipeline_bg(project_id: UUID, file_records: List[dict]):
    """Background task to execute the full 7-stage audit pipeline asynchronously."""
    temp_files: List[Path] = []
    output_dir = Path(tempfile.gettempdir()) / f"audit_output_{project_id}"
    
    try:
        # 1. Query Project & Client metadata to inject corporate name and audit year
        client_name = None
        audit_year = None
        
        project_res = supabase.table("projects").select("*").eq("id", str(project_id)).execute()
        if project_res.data:
            proj_data = project_res.data[0]
            audit_year = proj_data.get("audit_year")
            client_id = proj_data.get("client_id")
            
            if client_id:
                client_res = supabase.table("clients").select("name").eq("id", str(client_id)).execute()
                if client_res.data:
                    client_name = client_res.data[0].get("name")

        # 2. Download binary files from Supabase storage into local temp files
        for file_record in file_records:
            file_bytes = supabase.storage.from_(STORAGE_BUCKET).download(file_record["file_path"])
            suffix = f".{file_record['file_type']}"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(file_bytes)
            tmp.close()
            temp_files.append(Path(tmp.name))

        # 3. Execute the complete AuditService pipeline with metadata injection
        audit_output = AuditService.run_full_audit_pipeline(
            file_paths=temp_files,
            output_dir=output_dir,
            apply_scale=True,
            client_name=client_name,
            audit_year=audit_year
        )

        # 4. Upload generated deliverables (PDF & Excel Workpapers) to Supabase Storage
        deliverables = audit_output.get("deliverables", {})
        package_paths = deliverables.get("package_paths", {})
        
        pdf_local_path = package_paths.get("pdf_report") or deliverables.get("pdf_report")
        xlsx_local_path = package_paths.get("excel_workbook") or deliverables.get("excel_workbook")

        pdf_storage_path = f"{project_id}/reports/Audit_Report.pdf"
        xlsx_storage_path = f"{project_id}/reports/Audit_Workbook.xlsx"

        pdf_url = None
        xlsx_url = None

        if pdf_local_path and os.path.exists(pdf_local_path):
            with open(pdf_local_path, "rb") as f:
                pdf_bytes = f.read()
                try:
                    supabase.storage.from_(STORAGE_BUCKET).upload(
                        path=pdf_storage_path,
                        file=pdf_bytes,
                        file_options={"content-type": "application/pdf", "upsert": "true"}
                    )
                    pdf_url = _generate_signed_url(pdf_storage_path)
                except Exception as upload_err:
                    print(f"Failed to upload PDF deliverable: {str(upload_err)}")

        if xlsx_local_path and os.path.exists(xlsx_local_path):
            with open(xlsx_local_path, "rb") as f:
                xlsx_bytes = f.read()
                try:
                    supabase.storage.from_(STORAGE_BUCKET).upload(
                        path=xlsx_storage_path,
                        file=xlsx_bytes,
                        file_options={"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "upsert": "true"}
                    )
                    xlsx_url = _generate_signed_url(xlsx_storage_path)
                except Exception as upload_err:
                    print(f"Failed to upload Excel deliverable: {str(upload_err)}")

        # 5. Map output dictionaries, sanitize JSON types (Decimals -> floats), and persist into database
        result_payload = {
            "project_id": str(project_id),
            "verification_data": audit_output.get("verification"),
            "analytics_data": audit_output.get("analytics"),
            "forensics_data": audit_output.get("analytics", {}).get("forensics"),
            "forecast_data": audit_output.get("forecasting"),
            "deliverables": {
                "pdf_report_url": pdf_url,
                "excel_workbook_url": xlsx_url,
                "pdf_storage_path": pdf_storage_path,
                "excel_storage_path": xlsx_storage_path,
                "audit_status": audit_output.get("audit_status")
            }
        }

        sanitized_payload = sanitize_for_json(result_payload)

        try:
            supabase.table("audit_results").insert(sanitized_payload).execute()
        except Exception as db_err:
            print(f"Warning: Could not insert into 'audit_results' table: {str(db_err)}")

        # 6. Mark project status as completed
        supabase.table("projects").update({"status": "completed"}).eq("id", str(project_id)).execute()

    except Exception as e:
        # Mark project status as failed if an unhandled error occurs
        try:
            supabase.table("projects").update({"status": "failed"}).eq("id", str(project_id)).execute()
        except Exception:
            pass
        print(f"Background execution error for project {project_id}: {str(e)}")

    finally:
        # 7. Clean up temporary files safely from disk
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass


@router.post("/run/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_project_audit(project_id: UUID, background_tasks: BackgroundTasks):
    """Triggers the full 7-stage audit pipeline asynchronously in a background task."""
    
    # 1. Fetch all private files tied to this project
    files_res = supabase.table("files").select("*").eq("project_id", str(project_id)).execute()
    if not files_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No files found for this project. Upload financial documents first."
        )

    # 2. Update project status to in_progress
    try:
        supabase.table("projects").update({"status": "in_progress"}).eq("id", str(project_id)).execute()
    except Exception:
        pass

    # 3. Add task to FastAPI BackgroundTasks
    background_tasks.add_task(run_audit_pipeline_bg, project_id, files_res.data)

    # 4. Return immediate 202 Accepted response
    return {
        "status": "processing",
        "project_id": str(project_id),
        "message": "Audit pipeline execution started asynchronously in the background."
    }


@router.get("/results/{project_id}")
async def get_audit_results(project_id: UUID):
    """Fetches completed audit results from database for a project."""
    try:
        res = supabase.table("audit_results").select("*").eq("project_id", str(project_id)).order("created_at", desc=True).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No audit results found for this project. Check if processing is complete."
            )
        return res.data[0]
    except Exception as e:
        if "audit_results" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Table 'audit_results' missing in Supabase. Please run the SQL DDL migration script."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audit results: {str(e)}"
        )