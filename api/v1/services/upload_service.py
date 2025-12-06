import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from api.v1.models.upload import ImageUpload, UploadStatus, ProcessingLog
from api.v1.schemas.upload import UploadCreate, UploadUpdate
from api.utils.logger import logger


class UploadService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_upload(self, upload_data: UploadCreate, original_url: str) -> ImageUpload:
        """Create a new upload record"""
        upload = ImageUpload(
            id=str(uuid.uuid4()),
            original_filename=upload_data.original_filename,
            original_url=original_url,
            file_size=upload_data.file_size,
            mime_type=upload_data.mime_type,
            status=UploadStatus.PENDING
        )
        
        upload.add(self.db)
        self.db.commit()
        self.db.refresh(upload)
        
        logger.info(f"Created upload record: {upload.id}")
        return upload
    
    def get_upload(self, upload_id: str) -> Optional[ImageUpload]:
        """Get upload by ID"""
        return self.db.query(ImageUpload).filter(ImageUpload.id == upload_id).first()
    
    def update_upload_status(
        self, 
        upload_id: str, 
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[ImageUpload]:
        """Update upload status"""
        upload = self.get_upload(upload_id)
        if not upload:
            return None
        
        upload.status = status
        upload.error_message = error_message
        
        if status == UploadStatus.PROCESSING and not upload.processing_started_at:
            upload.processing_started_at = datetime.utcnow()
        elif status == UploadStatus.COMPLETED and not upload.processing_completed_at:
            upload.processing_completed_at = datetime.utcnow()
        
        upload.update(self.db)
        logger.info(f"Updated upload {upload_id} status to {status}")
        return upload
    
    def update_processed_urls(
        self,
        upload_id: str,
        thumbnail_url: Optional[str] = None,
        resized_url: Optional[str] = None,
        compressed_url: Optional[str] = None
    ) -> Optional[ImageUpload]:
        """Update upload with processed image URLs"""
        upload = self.get_upload(upload_id)
        if not upload:
            return None
        
        if thumbnail_url:
            upload.thumbnail_url = thumbnail_url
        if resized_url:
            upload.resized_url = resized_url
        if compressed_url:
            upload.compressed_url = compressed_url
        
        upload.update(self.db)
        logger.info(f"Updated processed URLs for upload {upload_id}")
        return upload
    
    def add_processing_log(
        self,
        upload_id: str,
        step: str,
        status: str,
        message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> ProcessingLog:
        """Add a processing log entry"""
        log = ProcessingLog(
            upload_id=upload_id,
            step=step,
            status=status,
            message=message,
            duration_ms=duration_ms
        )
        
        log.add(self.db)
        self.db.commit()
        self.db.refresh(log)
        
        logger.info(f"Added processing log for upload {upload_id}, step: {step}")
        return log
    
    def cleanup_failed_uploads(self, hours_old: int = 24) -> int:
        """Clean up failed uploads older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        
        # Find failed uploads
        failed_uploads = self.db.query(ImageUpload).filter(
            ImageUpload.status == UploadStatus.FAILED,
            ImageUpload.created_at < cutoff_time
        ).all()
        
        # Delete them
        for upload in failed_uploads:
            upload.delete(self.db)
        
        self.db.commit()
        logger.info(f"Cleaned up {len(failed_uploads)} failed uploads")
        return len(failed_uploads)