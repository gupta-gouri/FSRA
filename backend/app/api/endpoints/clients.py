from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.core.supabase import supabase
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse

router = APIRouter()

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(payload: ClientCreate):
    client_data = payload.model_dump(exclude_unset=True)
    res = supabase.table("clients").insert(client_data).execute()
    
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create client entity."
        )
    return res.data[0]

@router.get("/", response_model=List[ClientResponse])
async def list_clients():
    res = supabase.table("clients").select("*").order("created_at", desc=True).execute()
    return res.data

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: UUID):
    res = supabase.table("clients").select("*").eq("id", str(client_id)).execute()
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found."
        )
    return res.data[0]

@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: UUID, payload: ClientUpdate):
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update."
        )
    
    res = supabase.table("clients").update(update_data).eq("id", str(client_id)).execute()
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or update failed."
        )
    return res.data[0]

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: UUID):
    res = supabase.table("clients").delete().eq("id", str(client_id)).execute()
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found."
        )
    return None