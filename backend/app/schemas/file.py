from datetime import datetime
from typing import Optional, Literal
import uuid
from uuid import UUID
from pydantic import BaseModel, ConfigDict

FileType = Literal["xlsx", "xls", "pdf"]
FileStatus = Literal["uploaded", "processing", "parsed", "failed"]

class FileBase(BaseModel):
    filename: str
    file_type: FileType
    file_size_bytes: int
    status: FileStatus

class FileResponse(FileBase):
    id: UUID
    project_id: UUID
    file_path: str
    download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)