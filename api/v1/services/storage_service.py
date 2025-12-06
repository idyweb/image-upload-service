import io
import uuid
from typing import Optional, Tuple, BinaryIO
from datetime import datetime

from google.cloud import storage
from PIL import Image

# from app.core.config import settings
from utils.logger import logger


class StorageService:
    def __init__(self):
        # self.bucket_name = settings.GOOGLE_STORAGE_BUCKET
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)
    
    def generate_file_path(self, upload_id: str, filename: str, suffix: str = "") -> str:
        """Generate a structured file path in GCS"""
        date_str = datetime.now().strftime("%Y/%m/%d")
        if suffix:
            filename = f"{filename.rsplit('.', 1)[0]}_{suffix}.{filename.rsplit('.', 1)[1]}"
        return f"uploads/{date_str}/{upload_id}/{filename}"
    
    async def upload_file(
        self, 
        file_content: bytes, 
        upload_id: str, 
        original_filename: str,
        suffix: str = "",
        content_type: Optional[str] = None
    ) -> str:
        """Upload file to Google Cloud Storage"""
        try:
            file_path = self.generate_file_path(upload_id, original_filename, suffix)
            blob = self.bucket.blob(file_path)
            
            # Upload file
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            # Make blob publicly accessible (or use signed URLs in production)
            blob.make_public()
            
            logger.info(f"File uploaded to GCS: {file_path}")
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {str(e)}")
            raise
    
    async def upload_image(
        self,
        image: Image.Image,
        upload_id: str,
        original_filename: str,
        suffix: str = "",
        format: str = "JPEG",
        quality: int = 85
    ) -> str:
        """Upload PIL Image to Google Cloud Storage"""
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=format, quality=quality)
            img_byte_arr.seek(0)
            
            # Determine content type
            content_type = f"image/{format.lower()}"
            if format == "JPEG":
                content_type = "image/jpeg"
            
            # Upload to GCS
            return await self.upload_file(
                img_byte_arr.getvalue(),
                upload_id,
                original_filename,
                suffix,
                content_type
            )
            
        except Exception as e:
            logger.error(f"Failed to upload image to GCS: {str(e)}")
            raise
    
    async def delete_file(self, file_url: str) -> bool:
        """Delete file from Google Cloud Storage"""
        try:
            # Extract blob path from URL
            blob_path = file_url.replace(f"https://storage.googleapis.com/{self.bucket_name}/", "")
            blob = self.bucket.blob(blob_path)
            blob.delete()
            
            logger.info(f"File deleted from GCS: {blob_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from GCS: {str(e)}")
            return False


# Singleton instance
storage_service = StorageService()