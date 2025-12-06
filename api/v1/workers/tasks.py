import time
from typing import Optional
from contextlib import contextmanager

from api.db.database import get_db
from api.v1.services.upload_service import UploadService
from api.v1.services.storage_service import storage_service
from api.v1.workers.image_processor import ImageProcessor
from api.v1.models import UploadStatus
from api.utils.logger import logger


@contextmanager
def db_session():
    """Context manager for database session"""
    db = next(get_db())
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def process_image(upload_id: str) -> dict:
    """Process image: resize, compress, create thumbnail"""
    start_time = time.time()
    
    try:
        with db_session() as db:
            upload_service = UploadService(db)
            
            # Get upload record
            upload = upload_service.get_upload(upload_id)
            if not upload:
                raise ValueError(f"Upload not found: {upload_id}")
            
            # Update status to processing
            upload_service.update_upload_status(upload_id, UploadStatus.PROCESSING)
            upload_service.add_processing_log(upload_id, "start", "started", "Image processing started")
            
            # Download original image from storage
            logger.info(f"Starting processing for upload: {upload_id}")
            upload_service.add_processing_log(upload_id, "download", "started", "Downloading original image")
            
            # Note: In production, you'd download from GCS here
            # For now, we'll simulate processing
            
            # Simulate processing steps
            steps = [
                ("resize", "Resizing image"),
                ("compress", "Compressing image"),
                ("thumbnail", "Creating thumbnail"),
                ("upload", "Uploading processed images")
            ]
            
            for step, message in steps:
                step_start = time.time()
                upload_service.add_processing_log(upload_id, step, "started", message)
                
                # Simulate processing time
                time.sleep(1)
                
                step_duration = int((time.time() - step_start) * 1000)
                upload_service.add_processing_log(
                    upload_id, step, "completed", 
                    f"{message} completed", step_duration
                )
            
            # Update with processed URLs (simulated)
            # In production, you'd upload to GCS and get real URLs
            upload_service.update_processed_urls(
                upload_id,
                thumbnail_url=f"https://storage.googleapis.com/{storage_service.bucket_name}/thumbnails/{upload_id}.jpg",
                resized_url=f"https://storage.googleapis.com/{storage_service.bucket_name}/resized/{upload_id}.jpg",
                compressed_url=f"https://storage.googleapis.com/{storage_service.bucket_name}/compressed/{upload_id}.jpg"
            )
            
            # Update status to completed
            upload_service.update_upload_status(upload_id, UploadStatus.COMPLETED)
            
            total_duration = int((time.time() - start_time) * 1000)
            upload_service.add_processing_log(
                upload_id, "complete", "completed",
                f"Image processing completed in {total_duration}ms", total_duration
            )
            
            logger.info(f"Completed processing for upload: {upload_id}")
            
            return {
                "upload_id": upload_id,
                "status": "completed",
                "processing_time_ms": total_duration
            }
            
    except Exception as e:
        logger.error(f"Failed to process image {upload_id}: {str(e)}")
        
        # Update status to failed
        try:
            with db_session() as db:
                upload_service = UploadService(db)
                upload_service.update_upload_status(upload_id, UploadStatus.FAILED, str(e))
                upload_service.add_processing_log(upload_id, "error", "failed", str(e))
        except Exception as db_error:
            logger.error(f"Failed to update failed status: {str(db_error)}")
        
        raise