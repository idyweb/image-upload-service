import uuid
from datetime import datetime
from sqlalchemy import String, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base_model import Base, BaseModel


class UploadStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageUpload(BaseModel):
    __tablename__ = "image_uploads"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    original_url: Mapped[str] = mapped_column(Text)
    
    # Processed URLs
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=True)
    resized_url: Mapped[str] = mapped_column(Text, nullable=True)
    compressed_url: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), 
        default=UploadStatus.PENDING
    )
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Metadata
    file_size: Mapped[int] = mapped_column(nullable=True)  # in bytes
    mime_type: Mapped[str] = mapped_column(String(50), nullable=True)
    width: Mapped[int] = mapped_column(nullable=True)
    height: Mapped[int] = mapped_column(nullable=True)
    
    # Processing metadata
    processing_started_at: Mapped[datetime] = mapped_column(nullable=True)
    processing_completed_at: Mapped[datetime] = mapped_column(nullable=True)
    
    # Relationships
    processing_logs: Mapped[list["ProcessingLog"]] = relationship(
        back_populates="upload", 
        cascade="all, delete-orphan"
    )


class ProcessingLog(BaseModel):
    __tablename__ = "processing_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    upload_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("image_uploads.id", ondelete="CASCADE")
    )
    step: Mapped[str] = mapped_column(String(50))  # e.g., "download", "resize", "upload"
    status: Mapped[str] = mapped_column(String(20))  # "started", "completed", "failed"
    message: Mapped[str] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(nullable=True)  # processing duration
    
    # Relationships
    upload: Mapped["ImageUpload"] = relationship(back_populates="processing_logs")