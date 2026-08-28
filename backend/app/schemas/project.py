from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict

ProjectStatus = Literal["draft", "in_progress", "under_review", "completed"]

# Base shared fields
class ProjectBase(BaseModel):
    title: str
    audit_year: int
    status: ProjectStatus = "draft"
    description: Optional[str] = None

# Creation payload (requires client_id)
class ProjectCreate(ProjectBase):
    client_id: UUID

# Partial update payload
class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    audit_year: Optional[int] = None
    status: Optional[ProjectStatus] = None
    description: Optional[str] = None

# API Response model
class ProjectResponse(ProjectBase):
    id: UUID
    client_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)
