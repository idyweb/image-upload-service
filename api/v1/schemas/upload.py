from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class UploadBase(BaseModel):
    original_filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class UploadCreate(UploadBase):
    pass


class UploadUpdate(BaseModel):
    status: Optional[str] = None
    thumbnail_url: Optional[str] = None
    resized_url: Optional[str] = None
    compressed_url: Optional[str] = None
    error_message: Optional[str] = None


class UploadInDB(UploadBase):
    id: str
    original_url: str
    thumbnail_url: Optional[str] = None
    resized_url: Optional[str] = None
    compressed_url: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    upload_id: str
    status_url: str
    result_url: str
    original_url: str
    created_at: datetime


class UploadStatusResponse(BaseModel):
    upload_id: str
    status: str
    error_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UploadResultResponse(BaseModel):
    upload_id: str
    status: str
    original_url: str
    thumbnail_url: Optional[str] = None
    resized_url: Optional[str] = None
    compressed_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime