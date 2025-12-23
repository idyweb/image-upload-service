import time
from typing import Optional
from contextlib import contextmanager

from api.db.database import get_db
from api.v1.services.upload_service import UploadService
from api.v1.services.storage_service import storage_service
from api.v1.workers.image_processor import ImageProcessor
from api.v1.models.upload import UploadStatus
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
            
            logger.info(f"Starting processing for upload: {upload_id}")
            
            # ========= ACTUAL PROCESSING STARTS HERE =========
            
            # 1. Download original from GCS
            upload_service.add_processing_log(upload_id, "download", "started", "Downloading original image")
            
            # Extract filename from URL
            original_url = upload.original_url
            # Get the blob path from GCS URL
            # URL format: https://storage.googleapis.com/bucket-name/path/to/file.jpg
            bucket_name = storage_service.bucket_name
            blob_path = original_url.replace(f"https://storage.googleapis.com/{bucket_name}/", "")
            
            # Download the file
            blob = storage_service.bucket.blob(blob_path)
            image_bytes = blob.download_as_bytes()
            
            upload_service.add_processing_log(upload_id, "download", "completed", "Original image downloaded")
            
            # 2. Process the image
            upload_service.add_processing_log(upload_id, "process", "started", "Processing image")
            
            # Open image
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_bytes))
            original_filename = upload.original_filename
            
            # Resize
            upload_service.add_processing_log(upload_id, "resize", "started", "Resizing image")
            from api.v1.workers.image_processor import ImageProcessor
            processor = ImageProcessor()
            
            resized_image = processor.resize_image(image, (1200, 1200))
            upload_service.add_processing_log(upload_id, "resize", "completed", "Image resized")
            
            # Create thumbnail
            upload_service.add_processing_log(upload_id, "thumbnail", "started", "Creating thumbnail")
            thumbnail_image = processor.create_thumbnail(image, (150, 150))
            upload_service.add_processing_log(upload_id, "thumbnail", "completed", "Thumbnail created")
            
            # Compress (use resized image as compressed version)
            upload_service.add_processing_log(upload_id, "compress", "started", "Compressing image")
            compressed_image = processor.compress_image(resized_image, quality=85)
            upload_service.add_processing_log(upload_id, "compress", "completed", "Image compressed")
            
            # 3. Upload processed images to GCS
            upload_service.add_processing_log(upload_id, "upload", "started", "Uploading processed images")
            
            # Upload thumbnail
            thumbnail_url = storage_service.upload_image(
                thumbnail_image,
                upload_id,
                original_filename,
                suffix="thumbnail",
                format="JPEG",
                quality=85
            )
            
            # Upload resized version
            resized_url = storage_service.upload_image(
                resized_image,
                upload_id,
                original_filename,
                suffix="resized",
                format="JPEG",
                quality=85
            )
            
            # Upload compressed version
            compressed_url = storage_service.upload_image(
                compressed_image,
                upload_id,
                original_filename,
                suffix="compressed",
                format="JPEG",
                quality=85
            )
            
            upload_service.add_processing_log(upload_id, "upload", "completed", "All images uploaded")
            
            # ========= ACTUAL PROCESSING ENDS HERE =========
            
            # 4. Save REAL URLs to database
            upload_service.update_processed_urls(
                upload_id,
                thumbnail_url=thumbnail_url,
                resized_url=resized_url,
                compressed_url=compressed_url
            )
            
            # 5. Update status to completed
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