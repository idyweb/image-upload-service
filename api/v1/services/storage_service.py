import io
from datetime import datetime
from typing import Optional

from google.cloud import storage
from PIL import Image

from api.utils.config import settings
from api.utils.logger import logger


class StorageService:
    def __init__(self):
        self.bucket_name = settings.GOOGLE_STORAGE_BUCKET
        self._client = None
        self._bucket = None
        self._init_failed = False

    @property
    def client(self):
        """Lazily initialize Google Cloud Storage client."""
        if self._client is None and not self._init_failed:
            try:
                self._client = storage.Client()
                logger.info("Google Cloud Storage client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Cloud Storage client: {e}. "
                              f"Storage operations will fail unless credentials are configured.")
                self._init_failed = True
                self._client = None
        return self._client

    @property
    def bucket(self):
        """Lazily get bucket reference."""
        if self._bucket is None and self.client is not None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    def generate_file_path(self, upload_id: str, filename: str, suffix: str = "") -> str:
        """Generate file path in GCS."""
        date_str = datetime.now().strftime("%Y/%m/%d")
        name, ext = filename.rsplit(".", 1)

        if suffix:
            filename = f"{name}_{suffix}.{ext}"

        return f"uploads/{date_str}/{upload_id}/{filename}"

    def upload_file(
        self,
        file_content: bytes,
        upload_id: str,
        original_filename: str,
        suffix: str = "",
        content_type: Optional[str] = None,
    ) -> str:
        """Upload raw bytes to Google Cloud Storage."""
        try:
            if not self.client or not self.bucket:
                raise RuntimeError("Google Cloud Storage not configured. Please set up credentials.")
            
            file_path = self.generate_file_path(upload_id, original_filename, suffix)
            blob = self.bucket.blob(file_path)

            blob.upload_from_string(
                file_content,
                content_type=content_type,
            )

            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{file_path}"

            logger.info(f"File uploaded to GCS: {file_path}")
            return public_url

        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {str(e)}")
            raise

    def upload_image(
        self,
        image: Image.Image,
        upload_id: str,
        original_filename: str,
        suffix: str = "",
        format: str = "JPEG",
        quality: int = 85,
    ) -> str:
        """Upload a PIL Image to Google Cloud Storage."""
        try:
            img_io = io.BytesIO()
            
            # Handle RGBA to RGB conversion for JPEGs
            if format.upper() == "JPEG" and image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1]) # use alpha channel as mask
                image = background

            image.save(img_io, format=format, quality=quality)
            img_io.seek(0)

            content_type = f"image/{format.lower()}"
            if format.upper() == "JPEG":
                content_type = "image/jpeg"

            return self.upload_file(
                img_io.getvalue(),
                upload_id,
                original_filename,
                suffix,
                content_type,
            )

        except Exception as e:
            logger.error(f"Failed to upload image to GCS: {str(e)}")
            raise

    def delete_file(self, file_url: str) -> bool:
        """Delete a file from Google Cloud Storage."""
        try:
            if not self.client or not self.bucket:
                logger.warning("Cannot delete file: Google Cloud Storage not configured")
                return False
            
            prefix = f"https://storage.googleapis.com/{self.bucket_name}/"
            blob_path = file_url.replace(prefix, "")

            blob = self.bucket.blob(blob_path)
            blob.delete()

            logger.info(f"File deleted from GCS: {blob_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file from GCS: {str(e)}")
            return False


# Singleton instance
storage_service = StorageService()
