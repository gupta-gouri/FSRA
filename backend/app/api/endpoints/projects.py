from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from app.core.supabase import supabase
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()

@router.post("/", response_model = ProjectResponse, status_code = status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate):
    project_data = payload.model_dump(mode = "json", exclude_unset = True)
    res = supabase.table("projects").insert(project_data).execute()

    if not res.data:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Failed to create project."
        )
    return res.data[0]

@router.get("/", response_model = List[ProjectResponse])
async def list_projects(client_id: Optional[UUID] = Query(None, description = "Filter by client ID")):
    query = supabase.table("projects").select("*")
    if client_id:
        query = query.eq("client_id", str(client_id))

    res = query.order("created_at", desc = True).execute()
    return res.data

@router.get("/{project_id}", response_model = ProjectResponse)
async def get_project(project_id: UUID):
    res = supabase.table("projects").select("*").eq("id", str(project_id)).execute()
    if not res.data:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Project not found."
        )
    return res.data[0]

@router.patch("/{project_id}", response_model = ProjectResponse)
async def update_project(project_id: UUID, payload: ProjectUpdate):
    update_data = payload.model_dump(mode = "json", exclude_unset = True)
    if not update_data:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "No fields provided for update."
        )
    res = supabase.table("projects").update(update_data).eq("id", str(project_id)).execute()
    if not res.data:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Project not found or update failed."
        )
    return res.data[0]

@router.delete("/{project_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID):
    res = supabase.table("projects").delete().eq("id", str(project_id)).execute()
    if not res.data:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Project not found."
        )
    return None