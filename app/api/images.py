import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select

from app.db import session_scope
from app.models.image import Image
from app.schemas.common import SuccessResponse
from app.schemas.images import ImageListResponse, ImageResponse
from app.services.image_service import ImageService


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=ImageResponse,
    summary="Upload Image",
    description="Upload and compress an image. Returns stored image metadata.",
)
async def upload_image(
    file: UploadFile = File(...),
    compression_type: str = Form("menu_full"),
) -> ImageResponse:
    """Upload and compress an image."""
    try:
        # Process and compress image
        image_data = await ImageService.process_and_save_image(file=file, compression_type=compression_type)

        # Keep upload logs at DEBUG to reduce noise in production
        logger.debug(
            "Image uploaded: filename=%s, compressed_size_bytes=%s",
            file.filename,
            image_data["file_size"],
        )

        # Save to DB
        async with session_scope() as session:
            image = Image(**image_data)
            session.add(image)
            await session.flush()
            await session.refresh(image)

            created_ts = ImageService.timestamp_from_datetime(dt=image.created_at)

            return ImageResponse(
                id=image.id,
                filename=image.filename,
                original_filename=image.original_filename,
                file_size=image.file_size,
                mime_type=image.mime_type,
                uploaded_at=image.created_at,
                url=ImageService.get_image_url(image_id=image.id, created_at=created_ts),
            )

    except ValueError as e:
        # Validation/size/type errors and invalid images -> 400
        logger.info("Image upload rejected: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Upload error: %s", e)
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@router.get(
    "/",
    response_model=ImageListResponse,
    summary="List Images",
    description="List all stored images with metadata.",
)
async def get_all_images() -> ImageListResponse:
    """Get list of all images."""
    async with session_scope() as session:
        result = await session.execute(select(Image).order_by(Image.created_at.desc()))
        images = list(result.scalars().all())

        images_payload = [
            ImageResponse(
                id=img.id,
                filename=img.filename,
                original_filename=img.original_filename,
                file_size=img.file_size,
                mime_type=img.mime_type,
                uploaded_at=img.created_at,
                url=ImageService.get_image_url(
                    image_id=img.id, created_at=ImageService.timestamp_from_datetime(dt=img.created_at)
                ),
            )
            for img in images
        ]

        return ImageListResponse(images=images_payload, total=len(images_payload))


@router.delete(
    "/{image_id}",
    response_model=SuccessResponse,
    summary="Delete Image",
    description="Delete image by ID.",
)
async def delete_image(image_id: int) -> SuccessResponse:
    """Delete image."""
    async with session_scope() as session:
        # Fetch image
        image = await session.get(Image, image_id)
        if not image:
            logger.error("Image not found with ID: %s", image_id)
            raise HTTPException(status_code=404, detail="Image not found")

        # Delete from DB
        await session.delete(image)

        return SuccessResponse(message="Image deleted")
