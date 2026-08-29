import os
import uuid
from uuid import UUID
from typing import List
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from app.core.supabase import supabase
from app.schemas.file import FileResponse

router = APIRouter()

STORAGE_BUCKET = "audit-files"
ALLOWED_EXTENSIONS = {"xlsx", "xls", "pdf"}
SIGNED_URL_EXPIRY_SECONDS = 3600 # 1 hour secure link

def generate_signed_url(file_path: str) -> str:
    """Generates a secure temporary download link for private bucket files."""
    try:
        res = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(path = file_path, expires_in = SIGNED_URL_EXPIRY_SECONDS)
        return res.get("signedURL") or res.get("signedUrl")
    except Exception:
        return None

@router.post("/upload", response_model = FileResponse, status_code = status.HTTP_201_CREATED)
async def upload_file(project_id: UUID = Form(...), file: UploadFile = File(...)):

    # 1. Enfore strict Excel and PDF file extension check
    file_ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"Invalid file type '.{file_ext}'. Allowed formats are: Excel (.xlsx, .xls) or PDF (.pdf)"
        )

    # 2. Read and validate content
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Uploaded file is empty."
        )

    # 3. Path in private storgae: <project_id>/<uuid>_<filename>
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    storage_path = f"{project_id}/{unique_filename}"

    # 4. Upload to private Supabase storage bucket
    try:
        supabase.storage.from_(STORAGE_BUCKET).upload(path = storage_path, file = content, file_options = {"content-type": file.content_type or "application/octet-stream"})
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = f"Failed to upload a private storage: {str(e)}"
        )

    # 5. Insert DB Metadata
    file_record = {
        "project_id": str(project_id),
        "filename": file.filename,
        "file_path": storage_path,
        "file_type": file_ext,
        "file_size_bytes": file_size,
        "status": file.status
    }

    res = supabase.table("files").insert(file_record).execute()
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record file metadata."
        )

    data = res.data[0]
    data["download_url"] = generate_signed_url(storage_path)
    return data

@router.get("/", response_model=List[FileResponse])
async def list_files_for_project(project_id: UUID):
    res = supabase.table("files").select("*").eq("project_id", str(project_id)).order("created_at", desc=True).execute()
    
    files_with_urls = []
    for item in res.data:
        item["download_url"] = generate_signed_url(item["file_path"])
        files_with_urls.append(item)
        
    return files_with_urls

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: UUID):
    res = supabase.table("files").select("*").eq("id", str(file_id)).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File record not found.")
    
    file_info = res.data[0]

    # Remove from private storage
    try:
        supabase.storage.from_(STORAGE_BUCKET).remove([file_info["file_path"]])
    except Exception:
        pass

    # Remove DB row
    supabase.table("files").delete().eq("id", str(file_id)).execute()
    return None