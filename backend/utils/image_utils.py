import base64
import io
import requests
from PIL import Image
from typing import Optional, Tuple
from loguru import logger

from config.settings import settings

def validate_image_size(image_data: bytes) -> bool:
    """Validate image size against maximum allowed size"""
    return len(image_data) <= settings.MAX_FILE_SIZE

def validate_image_format(content_type: str) -> bool:
    """Validate image format against allowed types"""
    return content_type.lower() in [mime.lower() for mime in settings.ALLOWED_IMAGE_TYPES]

def encode_image_to_base64(image_data: bytes) -> str:
    """Encode image bytes to base64 string"""
    return base64.b64encode(image_data).decode('utf-8')

def decode_base64_image(base64_string: str) -> bytes:
    """Decode base64 string to image bytes"""
    # Remove data URL prefix if present
    if base64_string.startswith('data:'):
        base64_string = base64_string.split(',')[1]
    
    return base64.b64decode(base64_string)

def get_image_from_url(image_url: str) -> Optional[bytes]:
    """Download image from URL and return bytes"""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Validate content type
        content_type = response.headers.get('content-type', '')
        if not validate_image_format(content_type):
            logger.error(f"Invalid image format: {content_type}")
            return None
        
        # Validate size
        if not validate_image_size(response.content):
            logger.error(f"Image too large: {len(response.content)} bytes")
            return None
        
        return response.content
        
    except Exception as e:
        logger.error(f"Error downloading image from URL: {str(e)}")
        return None

def get_image_dimensions(image_data: bytes) -> Optional[Tuple[int, int]]:
    """Get image dimensions (width, height)"""
    try:
        image = Image.open(io.BytesIO(image_data))
        return image.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {str(e)}")
        return None

def resize_image(image_data: bytes, max_width: int = 1024, max_height: int = 1024) -> bytes:
    """Resize image to fit within maximum dimensions while maintaining aspect ratio"""
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Calculate new dimensions
        width, height = image.size
        aspect_ratio = width / height
        
        if width > max_width or height > max_height:
            if aspect_ratio > 1:  # Wider than tall
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:  # Taller than wide
                new_height = max_height
                new_width = int(max_height * aspect_ratio)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return image_data  # Return original if resize fails

def convert_to_jpeg(image_data: bytes) -> bytes:
    """Convert image to JPEG format"""
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Save as JPEG
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error converting image to JPEG: {str(e)}")
        return image_data  # Return original if conversion fails

def process_image_for_bedrock(image_data: bytes) -> str:
    """Process image for Bedrock API (resize, convert, encode)"""
    try:
        # Resize image if too large
        processed_image = resize_image(image_data, max_width=1024, max_height=1024)
        
        # Convert to JPEG
        processed_image = convert_to_jpeg(processed_image)
        
        # Encode to base64
        return encode_image_to_base64(processed_image)
        
    except Exception as e:
        logger.error(f"Error processing image for Bedrock: {str(e)}")
        raise Exception(f"Failed to process image: {str(e)}")

def get_image_info(image_data: bytes) -> dict:
    """Get comprehensive image information"""
    try:
        image = Image.open(io.BytesIO(image_data))
        
        return {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.width,
            'height': image.height,
            'has_transparency': image.mode in ('RGBA', 'LA', 'P'),
            'file_size': len(image_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting image info: {str(e)}")
        return {
            'error': str(e),
            'file_size': len(image_data)
        }

def extract_mime_type_from_base64(base64_string: str) -> str:
    """Extract MIME type from base64 data URL"""
    if base64_string.startswith('data:'):
        mime_part = base64_string.split(',')[0]
        if 'image/' in mime_part:
            return mime_part.split(':')[1].split(';')[0]
    
    return 'image/jpeg'  # Default fallback

def create_thumbnail(image_data: bytes, size: Tuple[int, int] = (200, 200)) -> bytes:
    """Create thumbnail of image"""
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Create thumbnail
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to JPEG
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error creating thumbnail: {str(e)}")
        raise Exception(f"Failed to create thumbnail: {str(e)}") 