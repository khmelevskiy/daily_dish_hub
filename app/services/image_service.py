import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Tuple

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


logger = logging.getLogger(__name__)

try:  # noqa: SIM105 - support graceful degradation if heif is not available
    from pillow_heif import register_heif_opener  # type: ignore
except ImportError:  # pragma: no cover - depends on environment
    register_heif_opener = None  # type: ignore[assignment]
    _HEIF_SUPPORTED = False
    logger.info("pillow-heif not available; AVIF/HEIF input will be disabled")
else:
    try:
        register_heif_opener()
    except Exception as exc:  # pragma: no cover - depends on environment
        logger.warning("Failed to enable HEIF support, continuing without it: %s", exc)
        _HEIF_SUPPORTED = False
    else:
        _HEIF_SUPPORTED = True

_BASE_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
}
_HEIF_ALLOWED_CONTENT_TYPES = {
    "image/avif",
    "image/heic",
    "image/heif",
}

if _HEIF_SUPPORTED:
    _ALLOWED_CONTENT_TYPES = frozenset(_BASE_ALLOWED_CONTENT_TYPES | _HEIF_ALLOWED_CONTENT_TYPES)
else:
    _ALLOWED_CONTENT_TYPES = frozenset(_BASE_ALLOWED_CONTENT_TYPES)


MAX_TOTAL_PIXELS = 80_000_000  # ~28MP×3; blocks decompression bombs early


class ImageService:
    heif_supported: bool = _HEIF_SUPPORTED
    # Allowed content types (restrictive allowlist)
    ALLOWED_CONTENT_TYPES = _ALLOWED_CONTENT_TYPES

    # Compression settings for different use-cases
    COMPRESSION_SETTINGS = {
        "menu_thumbnails": {
            "max_size": (300, 300),
            "quality": 80,
            "format": "JPEG",
        },  # Thumbnails in lists
        "menu_full": {
            "max_size": (800, 800),
            "quality": 85,
            "format": "JPEG",
        },  # Full images for menu
        "admin_preview": {
            "max_size": (1200, 1200),
            "quality": 90,
            "format": "JPEG",
        },  # Admin preview
    }

    @staticmethod
    async def compress_image(file_data: bytes, max_size: Tuple[int, int] = (800, 800), quality: int = 85) -> bytes:
        """Compress image to the specified size and quality.

        Notes:
        - All inputs are decoded (JPEG/PNG/WEBP/TIFF/HEIC/AVIF) and re-encoded to JPEG.
        - Alpha channels are removed (RGBA/LA/P -> RGB) before save.

        """
        try:
            # Open image
            image = Image.open(io.BytesIO(file_data))
        except UnidentifiedImageError as e:
            raise ValueError("Invalid image") from e
        except Exception as e:
            # Wrap any other decoder errors as invalid image
            raise ValueError("Invalid image") from e

        # Convert to RGB if needed
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")

        # Basic decompression bomb guard (width * height check)
        if image.width is None or image.height is None:
            raise ValueError("Invalid image dimensions")
        if image.width * image.height > MAX_TOTAL_PIXELS:
            raise ValueError("Image resolution too large")

        # Resize preserving aspect ratio
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save to bytes with compression
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)

        return output.getvalue()

    @staticmethod
    async def process_and_save_image(file: UploadFile, compression_type: str = "menu_full") -> dict:
        """Process and prepare image for saving into DB.

        - Accepts JPEG/PNG/WEBP/TIFF/HEIC/HEIF/AVIF as input (AVIF/HEIF via pillow-heif).
        - Always re-encodes to JPEG for storage uniformity.
        - Returns dict suitable for DB insertion (file_data is JPEG, mime_type is image/jpeg),
        with a generated filename that always ends in `.jpg`.
        """
        # Validate file type (allowlist)
        allowed_labels = ["JPEG", "PNG", "WEBP", "TIFF"]
        if ImageService.heif_supported:
            allowed_labels.append("AVIF/HEIF")

        if not file.content_type or file.content_type.lower() not in ImageService.ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Only {', '.join(allowed_labels)} images are allowed")

        # Read file and enforce size limit from settings
        file_data = await file.read()
        max_bytes = int(settings.max_upload_size_mb) * 1024 * 1024
        if len(file_data) > max_bytes:
            raise ValueError("File too large")

        # Select compression settings
        if compression_type not in ImageService.COMPRESSION_SETTINGS:
            raise ValueError(f"Unsupported compression type: {compression_type}")
        comp = ImageService.COMPRESSION_SETTINGS[compression_type]

        # Compress image (catch invalid image errors)
        compressed_data = await ImageService.compress_image(
            file_data=file_data, max_size=comp["max_size"], quality=comp["quality"]
        )

        # Create unique filename (always use .jpg since we re-encode to JPEG)
        filename = f"{uuid.uuid4()}.jpg"

        return {
            "filename": filename,
            "original_filename": file.filename,
            "file_data": compressed_data,
            "file_size": len(compressed_data),
            "mime_type": "image/jpeg",
        }

    @staticmethod
    def get_image_url(image_id: int, created_at: int | None = None) -> str:
        """Return URL to fetch the image."""
        if created_at is not None:
            return f"/images/{image_id}?v={created_at}"

        return f"/images/{image_id}"

    @staticmethod
    def ensure_utc(dt: datetime) -> datetime:
        """Return datetime aware of UTC (treat naive values as UTC)."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    @staticmethod
    def timestamp_from_datetime(dt: datetime | None) -> int | None:
        """Convert DB datetime (naive or aware) to a stable UTC unix timestamp."""
        if dt is None:
            return None

        return int(ImageService.ensure_utc(dt=dt).timestamp())
