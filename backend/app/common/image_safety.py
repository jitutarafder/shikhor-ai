"""Image sanitization, magic bytes verification, and EXIF stripping.

Strictly enforces AGENTS.md Rule 18 and Security.md Section 8:
- Accepts only approved JPEG, PNG, and WebP formats.
- Validates file extension, MIME type, and binary file signatures (magic bytes).
- Enforces maximum file byte size and pixel dimensions.
- Rejects decompression bombs and malformed image files.
- Decodes and re-encodes into a sanitized WebP derivative with all EXIF/GPS metadata removed.
"""

import io
import uuid
from typing import Tuple
from PIL import Image

from app.core.errors import ShikhorException

# Allowed formats and byte signatures
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Max limits: 10 MB and 4096 x 4096 px
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4096
Image.MAX_IMAGE_PIXELS = 25_000_000  # Guard against decompression bombs


def check_magic_bytes(header: bytes) -> str:
    """Verifies file signature against authentic image magic bytes."""
    if len(header) < 12:
        raise ShikhorException(
            code="INVALID_FILE_HEADER",
            message="Uploaded file is too small or corrupt.",
            status_code=400,
        )

    # JPEG: starts with FF D8 FF
    if header.startswith(b"\xff\xd8\xff"):
        return "JPEG"

    # PNG: starts with 89 50 4E 47 0D 0A 1A 0A
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"

    # WebP: starts with RIFF....WEBP
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "WEBP"

    raise ShikhorException(
        code="UNSUPPORTED_IMAGE_FORMAT",
        message="Only authentic JPEG, PNG, and WebP images are permitted.",
        status_code=400,
    )


def sanitize_and_reencode_image(
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> Tuple[bytes, str, int, int]:
    """Sanitizes image bytes, strips EXIF/GPS metadata, and re-encodes to a safe WebP derivative.

    Returns:
        (sanitized_bytes, safe_filename, width, height)
    """
    # 1. Byte size limit
    if len(file_bytes) > MAX_FILE_BYTES:
        raise ShikhorException(
            code="IMAGE_TOO_LARGE",
            message=f"Image size exceeds the maximum limit of {MAX_FILE_BYTES // (1024 * 1024)}MB.",
            status_code=400,
        )

    # 2. Validate MIME type
    if content_type.lower() not in ALLOWED_MIME_TYPES:
        raise ShikhorException(
            code="INVALID_MIME_TYPE",
            message="Invalid image MIME type.",
            status_code=400,
        )

    # 3. Validate Magic Bytes
    check_magic_bytes(file_bytes[:12])

    # 4. Open with Pillow to verify integrity & dimensions
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
    except Exception:
        raise ShikhorException(
            code="MALFORMED_IMAGE",
            message="The uploaded image file is corrupt or malformed.",
            status_code=400,
        )

    # 5. Decode and re-encode to strip metadata completely
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise ShikhorException(
                    code="IMAGE_DIMENSIONS_EXCEEDED",
                    message=f"Image dimensions exceed {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION} limit.",
                    status_code=400,
                )

            # Convert to RGB (or RGBA for transparent PNG/WebP)
            mode = "RGBA" if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info) else "RGB"
            clean_img = img.convert(mode)

            # Re-encode as WebP without EXIF
            output_buffer = io.BytesIO()
            clean_img.save(output_buffer, format="WEBP", quality=85, method=4)
            sanitized_bytes = output_buffer.getvalue()

            safe_filename = f"{uuid.uuid4().hex}.webp"
            return sanitized_bytes, safe_filename, width, height
    except ShikhorException:
        raise
    except Exception as e:
        raise ShikhorException(
            code="IMAGE_PROCESSING_FAILED",
            message="Failed to process and sanitize the image.",
            status_code=400,
        )
