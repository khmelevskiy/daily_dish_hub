from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ImageResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    url: str
    file_size: int
    mime_type: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageListResponse(BaseModel):
    images: list[ImageResponse]
    total: int


__all__ = ["ImageResponse", "ImageListResponse"]
