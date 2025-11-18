"""
File-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FileBase(BaseModel):
    """Base file schema"""

    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., max_length=50, description="MIME type or file extension")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    description: Optional[str] = Field(None, max_length=500)


class FileCreate(FileBase):
    """Schema for file creation"""

    file_path: str = Field(..., description="Storage path or URL")
    file_hash: str = Field(..., description="File hash for integrity verification")
    related_entity_type: Optional[str] = Field(
        None, description="Entity type: project, task, document, message"
    )
    related_entity_id: Optional[int] = Field(None, description="ID of related entity")


class FileUpdate(BaseModel):
    """Schema for file update"""

    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class FileResponse(BaseModel):
    """Schema for file response"""

    id: int
    filename: str
    file_type: str
    file_size: int
    file_path: str
    file_hash: str
    description: Optional[str]
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    owner_id: int
    download_count: int = 0
    is_public: bool = False
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class FileUploadResponse(BaseModel):
    """Schema for file upload response"""

    file_id: int
    filename: str
    file_size: int
    file_type: str
    upload_url: str
    message: str = "File uploaded successfully"

    model_config = ConfigDict(from_attributes=True)


class FileDownloadResponse(BaseModel):
    """Schema for file download response"""

    filename: str
    file_type: str
    file_size: int
    download_url: str

    model_config = ConfigDict(from_attributes=True)


class FileSearchFilter(BaseModel):
    """Schema for file search and filtering"""

    filename: Optional[str] = Field(None, description="Search by filename")
    file_type: Optional[str] = None
    owner_id: Optional[int] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    min_size: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
