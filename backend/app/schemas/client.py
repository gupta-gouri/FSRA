from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr

# Base shared properties
class ClientBase(BaseModel):
    name: str
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    contact_email: Optional[EmailStr] = None

# Properties required on creation
class ClientCreate(ClientBase):
    pass

# Properties updatable via PATCH/PUT
class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    contact_email: Optional[EmailStr] = None

# Response model returned to clients
class ClientResponse(ClientBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)