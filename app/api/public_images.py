import logging
import re
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import select

from app.db import session_scope
from app.models.image import Image
from app.services.image_service import ImageService


logger = logging.getLogger(__name__)

router = APIRouter()


def _sanitize_filename_for_header(name: str, max_len: int = 70) -> str:
    """Return an ASCII-safe filename for HTTP headers.

    - Removes CR/LF and control characters
    - Drops quotes and backslashes
    - Allows only [A-Za-z0-9._-]
    - Truncates to `max_len` (keep extension if present)
    - Prevents empty/hidden names
    """
    if not name:
        return "file"

    # Remove control characters including CR/LF
    name = re.sub(r"[\r\n\t\x00-\x1F\x7F]", "", name)
    # Remove path separators
    name = name.replace("/", "_").replace("\\", "_")
    # Remove quotes/backslashes explicitly
    name = name.replace('"', "").replace("'", "")
    # Allow only safe chars
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    # Collapse consecutive underscores
    name = re.sub(r"_+", "_", name)
    # Normalize leading characters only on the basename (keep extension)
    base, dot, ext = name.rpartition(".")
    if dot:  # has extension
        if base == "":
            # Hidden file like ".env" -> strip leading dot, keep ext only
            name = ext or "file"
        else:
            safe_base = base.lstrip("._")
            name = f"{(safe_base or 'file')}.{ext}"
    else:
        name = name.lstrip("._") or "file"

    if len(name) <= max_len:
        return name

    # Preserve extension when truncating
    base, dot, ext = name.rpartition(".")
    if dot:
        ext = (ext or "")[:10]  # keep extension sane
        remaining = max(1, max_len - (1 + len(ext)))
        base = base[:remaining]

        return f"{base}.{ext}"

    return name[:max_len]


@router.get(
    "/{image_id}",
    summary="Get Public Image",
    description="Return public image binary by ID with cache headers.",
)
async def get_image(image_id: int, request: Request) -> Response:
    """Public endpoint to fetch an image by ID."""
    async with session_scope() as session:
        # Fetch image from DB
        result = await session.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()

        if not image:
            # 404 is common for stale links; keep log level low to avoid noise
            logger.info("Public image not found: id=%s", image_id)
            raise HTTPException(status_code=404, detail="Image not found")

        # Return image content
        safe_name = _sanitize_filename_for_header(name=image.original_filename or "image.jpg")
        created_at_utc = ImageService.ensure_utc(dt=image.created_at)
        created_ts = ImageService.timestamp_from_datetime(dt=image.created_at)

        etag_ts = created_ts if created_ts is not None else 0

        etag_value = f'"{image.id}-{etag_ts}"'
        headers = {
            "Content-Disposition": f"inline; filename={safe_name}",
            "Cache-Control": "public, max-age=604800",  # cache for 7 days
            "Last-Modified": created_at_utc.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "ETag": etag_value,
            "Expires": (created_at_utc + timedelta(days=7)).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        }

        if_none_match = request.headers.get("if-none-match")
        if if_none_match and etag_value in {tag.strip() for tag in if_none_match.split(",")}:
            return Response(status_code=304, headers=headers)

        if_modified_since = request.headers.get("if-modified-since")
        if if_modified_since:
            try:
                client_ts = parsedate_to_datetime(if_modified_since)
            except (TypeError, ValueError):
                client_ts = None
            if client_ts:
                if client_ts.tzinfo is None:
                    client_ts = client_ts.replace(tzinfo=timezone.utc)
                else:
                    client_ts = client_ts.astimezone(timezone.utc)
                if client_ts >= created_at_utc.replace(microsecond=0):
                    return Response(status_code=304, headers=headers)

        return Response(content=image.file_data, media_type=image.mime_type, headers=headers)
