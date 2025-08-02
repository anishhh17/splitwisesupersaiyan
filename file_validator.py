from fastapi import HTTPException, UploadFile
from typing import Set, Optional
from PIL import Image
import io

class FileValidator:
    # Allowed MIME types for images
    ALLOWED_IMAGE_TYPES: Set[str] = {
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/gif',
        'image/bmp',
        'image/webp',
        'image/tiff',
        'image/tif'
    }
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS: Set[str] = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'
    }
    
    # Maximum file size (10MB by default)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    
    # Image format signatures (magic bytes) for validation
    IMAGE_SIGNATURES = {
        b'\xff\xd8\xff': 'image/jpeg',  # JPEG
        b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a': 'image/png',  # PNG
        b'\x47\x49\x46\x38\x37\x61': 'image/gif',  # GIF87a
        b'\x47\x49\x46\x38\x39\x61': 'image/gif',  # GIF89a
        b'\x42\x4d': 'image/bmp',  # BMP
        b'\x52\x49\x46\x46': 'image/webp',  # WEBP (partial check)
        b'\x49\x49\x2a\x00': 'image/tiff',  # TIFF (little endian)
        b'\x4d\x4d\x00\x2a': 'image/tiff',  # TIFF (big endian)
    }
    
    # Default image dimension constraints
    MIN_IMAGE_DIMENSION = 10  # pixels
    MAX_IMAGE_DIMENSION = 10000  # pixels
    
    @staticmethod
    def validate_image_dimensions(img: Image.Image, 
                                  min_dimension: int = None, 
                                  max_dimension: int = None) -> None:
        """
        Validate image dimensions against min and max constraints
        
        Args:
            img: PIL Image object
            min_dimension: Minimum allowed dimension in pixels
            max_dimension: Maximum allowed dimension in pixels
            
        Raises:
            HTTPException: If image dimensions are outside allowed range
        """
        min_dimension = min_dimension or FileValidator.MIN_IMAGE_DIMENSION
        max_dimension = max_dimension or FileValidator.MAX_IMAGE_DIMENSION
        
        width, height = img.size
        
        if width > max_dimension or height > max_dimension:
            raise HTTPException(
                status_code=400,
                detail=f"Image dimensions too large. Maximum: {max_dimension}x{max_dimension} pixels"
            )
            
        if width < min_dimension or height < min_dimension:
            raise HTTPException(
                status_code=400,
                detail=f"Image too small. Minimum dimensions: {min_dimension}x{min_dimension} pixels"
            )
    
    @staticmethod
    def detect_mime_type_from_content(content: bytes) -> Optional[str]:
        """
        Detect MIME type from file content using magic bytes
        """
        for signature, mime_type in FileValidator.IMAGE_SIGNATURES.items():
            if content.startswith(signature):
                # Special handling for WEBP
                if mime_type == 'image/webp':
                    # WEBP files start with RIFF signature and have WEBP at position 8-12
                    if content.startswith(b'\x52\x49\x46\x46') and len(content) >= 12 and content[8:12] == b'WEBP':
                        return 'image/webp'
                else:
                    return mime_type
        
        # Fallback to PIL detection if magic bytes didn't work
        try:
            with Image.open(io.BytesIO(content)) as img:
                format = img.format
                if format:
                    format_lower = format.lower()
                    # Map PIL format to MIME type
                    format_to_mime = {
                        'jpeg': 'image/jpeg',
                        'jpg': 'image/jpeg',
                        'png': 'image/png',
                        'gif': 'image/gif',
                        'bmp': 'image/bmp',
                        'webp': 'image/webp',
                        'tiff': 'image/tiff'
                    }
                    return format_to_mime.get(format_lower)
        except:
            pass
        
        return None
    
    @staticmethod
    async def validate_image_file(
        file: UploadFile,
        max_size: Optional[int] = None,
        allowed_types: Optional[Set[str]] = None,
        enforce_extension: bool = True
    ) -> bytes:
        """
        Validate that uploaded file is a valid image
        
        Args:
            file: FastAPI UploadFile object
            max_size: Maximum file size in bytes (optional)
            allowed_types: Set of allowed MIME types (optional)
            
        Returns:
            File content as bytes if valid
            
        Raises:
            HTTPException: If file is invalid
        """
        max_size = max_size or FileValidator.MAX_FILE_SIZE
        allowed_types = allowed_types or FileValidator.ALLOWED_IMAGE_TYPES
        
        # Read file content
        try:
            content = await file.read()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
        # Reset file pointer for potential re-reading
        await file.seek(0)
        
        # 1. Check file size
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size allowed: {max_size / (1024*1024):.1f}MB"
            )
        
        # 2. Check if file is empty
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # 3. Validate file extension if enforced
        file_ext = None
        if file.filename:
            file_ext = '.' + file.filename.lower().split('.')[-1] if '.' in file.filename else ''
            
            if enforce_extension and file_ext not in FileValidator.ALLOWED_EXTENSIONS:
                # Check if the file content is actually a valid image despite the extension
                content_is_valid_image = False
                try:
                    with Image.open(io.BytesIO(content)) as img:
                        # If we can open it as an image, it might be valid despite the extension
                        content_is_valid_image = img.format is not None
                except:
                    pass
                
                if not content_is_valid_image:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid file extension. Allowed: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}"
                    )
        
        # 4. Check MIME type using magic bytes detection
        detected_mime = FileValidator.detect_mime_type_from_content(content)
        
        # Also check the content-type header as fallback
        content_type = file.content_type
        
        # Verify at least one method detects a valid image type
        valid_mime_detected = detected_mime and detected_mime in allowed_types
        valid_content_type = content_type and content_type in allowed_types
        
        if not (valid_mime_detected or valid_content_type):
            error_msg = "Invalid file type."
            if detected_mime:
                error_msg += f" Detected: {detected_mime}."
            if content_type:
                error_msg += f" Content-Type: {content_type}."
            error_msg += f" Allowed types: {', '.join(allowed_types)}"
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 5. Validate that it's actually a readable image using PIL
        try:
            # First just verify the image is valid
            with Image.open(io.BytesIO(content)) as img:
                # Try to verify the image
                img.verify()
                
            # Re-open for format checking (verify() closes the image)
            with Image.open(io.BytesIO(content)) as img:
                # Use thumbnail to efficiently check dimensions without loading entire image
                # This is especially important for large images
                img.draft(mode='RGB', size=(100, 100))  # Efficient image loading
                
                # Check image dimensions using our utility method
                FileValidator.validate_image_dimensions(img)
                
        except HTTPException:
            # Re-raise our own HTTP exceptions
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or corrupted image file: {str(e)}"
            )
        
        return content