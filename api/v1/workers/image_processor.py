import io
import time
from typing import Tuple, Optional
from PIL import Image, UnidentifiedImageError

from api.utils.config import settings
from api.v1.services.storage_service import storage_service
from api.utils.logger import logger


class ImageProcessor:
    @staticmethod
    def validate_image(image_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """Validate image file"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()  # Verify it's a valid image
            
            # Check image format
            if image.format not in ["JPEG", "PNG", "WEBP", "GIF"]:
                return False, f"Unsupported image format: {image.format}"
            
            # Check image size
            if len(image_bytes) > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
                return False, f"Image too large. Max size: {settings.MAX_IMAGE_SIZE_MB}MB"
            
            return True, None
            
        except UnidentifiedImageError:
            return False, "Invalid image file"
        except Exception as e:
            return False, f"Image validation failed: {str(e)}"
    
    @staticmethod
    def resize_image(image: Image.Image, max_size: Tuple[int, int]) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        original_width, original_height = image.size
        max_width, max_height = max_size
        
        # Calculate new dimensions
        ratio = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        logger.info(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
        
        return resized_image
    
    @staticmethod
    def compress_image(image: Image.Image, format: str = "JPEG", quality: int = 85) -> Image.Image:
        """Compress image by saving to buffer with lower quality"""
        buffer = io.BytesIO()
        format = format.upper()
        
        if format in ["JPEG", "WEBP"]:
            image.save(buffer, format=format, quality=quality, optimize=True)
        elif format == "PNG":
            image.save(buffer, format="PNG", optimize=True)
        else:
            image.save(buffer, format=format)
        
        buffer.seek(0)
        compressed_image = Image.open(buffer)
        logger.info(f"Compressed image to format {format} with quality {quality}")
        return compressed_image
    
    @staticmethod
    def create_thumbnail(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """Create a square thumbnail with cropping"""
        # Create thumbnail
        image.thumbnail(size, Image.LANCZOS)
        
        # If we want a square thumbnail, we need to crop
        if image.size[0] != image.size[1]:
            # Crop to center square
            width, height = image.size
            new_size = min(width, height)
            
            left = (width - new_size) / 2
            top = (height - new_size) / 2
            right = (width + new_size) / 2
            bottom = (height + new_size) / 2
            
            image = image.crop((left, top, right, bottom))
        
        logger.info(f"Created thumbnail: {image.size}")
        return image
    
    @staticmethod
    def get_image_format(mime_type: str) -> str:
        """Convert MIME type to PIL format"""
        format_map = {
            "image/jpeg": "JPEG",
            "image/png": "PNG",
            "image/webp": "WEBP",
            "image/gif": "GIF"
        }
        return format_map.get(mime_type, "JPEG")