from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
import uuid
from api.db.database import get_db
from api.v1.services.upload_service import UploadService
from api.v1.services.storage_service import storage_service
from api.v1.schemas.upload import UploadCreate
from api.v1.workers.celery_app import process_image_task
from api.v1.schemas.upload import UploadResponse, UploadStatusResponse, UploadResultResponse
from api.utils.responses import success_response, fail_response
from api.utils.logger import logger
from api.utils.config import settings

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an image for processing"""
    try:
        # Validate file type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            return fail_response(400, f"File type not allowed. Allowed types: {settings.ALLOWED_IMAGE_TYPES}")
        
        # Read file
        contents = await file.read()
        file_size = len(contents)
        
        # Validate file size
        max_size_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            return fail_response(400, f"File too large. Max size: {settings.MAX_IMAGE_SIZE_MB}MB")
        
        # Reset file pointer
        await file.seek(0)
        
        # Create upload service
        upload_service = UploadService(db)
        
        # Upload original file to storage
        upload_id = str(uuid.uuid4())
        original_url = await run_in_threadpool(
            storage_service.upload_file,
            contents, upload_id, file.filename
        )
        
        # Create upload record

        upload_data = UploadCreate(
            original_filename=file.filename,
            file_size=file_size,
            mime_type=file.content_type
        )
        
        upload = upload_service.create_upload(upload_data, original_url)
        
        # Start background processing
        process_image_task.delay(upload.id)
        
        # Return response
        return success_response(
            202,
            "Image uploaded successfully. Processing started.",
            UploadResponse(
                upload_id=upload.id,
                status_url=f"/upload/{upload.id}/status",
                result_url=f"/upload/{upload.id}/result",
                original_url=upload.original_url,
                created_at=upload.created_at
            ).dict()
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return fail_response(500, "Failed to upload image", {"error": str(e)})


@router.get("/upload/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """Get processing status of an upload"""
    try:
        upload_service = UploadService(db)
        upload = upload_service.get_upload(upload_id)
        
        if not upload:
            return fail_response(404, "Upload not found")
        
        return success_response(
            200,
            "Status retrieved successfully",
            UploadStatusResponse(
                upload_id=upload.id,
                status=upload.status,
                error_message=upload.error_message,
                processing_started_at=upload.processing_started_at,
                processing_completed_at=upload.processing_completed_at,
                created_at=upload.created_at,
                updated_at=upload.updated_at
            ).dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}")
        return fail_response(500, "Failed to get status", {"error": str(e)})


@router.get("/upload/{upload_id}/result", response_model=UploadResultResponse)
async def get_upload_result(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """Get processing result of an upload"""
    try:
        upload_service = UploadService(db)
        upload = upload_service.get_upload(upload_id)
        
        if not upload:
            return fail_response(404, "Upload not found")
        
        if upload.status != "completed":
            return fail_response(400, "Processing not completed yet")
        
        return success_response(
            200,
            "Result retrieved successfully",
            UploadResultResponse(
                upload_id=upload.id,
                status=upload.status,
                original_url=upload.original_url,
                thumbnail_url=upload.thumbnail_url,
                resized_url=upload.resized_url,
                compressed_url=upload.compressed_url,
                created_at=upload.created_at,
                updated_at=upload.updated_at
            ).dict()
        )
        
    except Exception as e:
        logger.error(f"Failed to get result: {str(e)}")
        return fail_response(500, "Failed to get result", {"error": str(e)})


@router.delete("/upload/{upload_id}")
async def delete_upload(
    upload_id: str,
    db: Session = Depends(get_db)
):
    """Delete an upload and its files"""
    try:
        upload_service = UploadService(db)
        upload = upload_service.get_upload(upload_id)
        
        if not upload:
            return fail_response(404, "Upload not found")
        
        # Delete files from storage
        urls_to_delete = [
            upload.original_url,
            upload.thumbnail_url,
            upload.resized_url,
            upload.compressed_url
        ]
        
        for url in urls_to_delete:
            if url:
                await run_in_threadpool(storage_service.delete_file, url)
        
        # Delete from database
        upload.delete(db)
        
        return success_response(200, "Upload deleted successfully")
        
    except Exception as e:
        logger.error(f"Failed to delete upload: {str(e)}")
        return fail_response(500, "Failed to delete upload", {"error": str(e)})