#!/usr/bin/env python3
"""Unit tests for ImageService (no server required).

Validates that inputs are re-encoded to JPEG and filenames end with .jpg,
and that unsupported content-types are rejected.
"""

import io
import sys

import pytest
from PIL import Image
from starlette.datastructures import Headers


@pytest.mark.asyncio
async def test_process_and_save_image_png_to_jpeg() -> None:
    from fastapi import UploadFile

    from app.services.image_service import ImageService

    # Create an in-memory PNG image
    buf = io.BytesIO()
    img = Image.new("RGBA", (50, 30), color=(10, 20, 30, 255))
    img.save(buf, format="PNG")
    buf.seek(0)

    headers = Headers({"content-type": "image/png"})
    upload = UploadFile(file=buf, filename="sample.png", headers=headers)

    data = await ImageService.process_and_save_image(upload)

    assert data["mime_type"] == "image/jpeg"
    assert data["filename"].endswith(".jpg")
    assert data["file_size"] > 0


@pytest.mark.asyncio
async def test_process_and_save_image_rejects_unsupported_type() -> None:
    from fastapi import UploadFile

    from app.services.image_service import ImageService

    buf = io.BytesIO(b"not an image")
    headers = Headers({"content-type": "application/octet-stream"})
    upload = UploadFile(file=buf, filename="payload.bin", headers=headers)

    with pytest.raises(ValueError):
        await ImageService.process_and_save_image(upload)


@pytest.mark.asyncio
async def test_process_and_save_image_rejects_unknown_compression_type() -> None:
    from fastapi import UploadFile

    from app.services.image_service import ImageService

    buf = io.BytesIO()
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(buf, format="JPEG")
    buf.seek(0)

    headers = Headers({"content-type": "image/jpeg"})
    upload = UploadFile(file=buf, filename="photo.jpg", headers=headers)

    with pytest.raises(ValueError) as exc:
        await ImageService.process_and_save_image(upload, compression_type="does-not-exist")

    assert "Unsupported compression type" in str(exc.value)


@pytest.mark.asyncio
async def test_upload_image_returns_400_for_invalid_compression(monkeypatch) -> None:
    from fastapi import HTTPException, UploadFile

    from app.api import images as images_api

    async def fake_process_and_save_image(file, compression_type="menu_full"):
        raise ValueError("Unsupported compression type: bad")

    monkeypatch.setattr(images_api.ImageService, "process_and_save_image", fake_process_and_save_image)

    buf = io.BytesIO(b"fake")
    headers = Headers({"content-type": "image/jpeg"})
    upload = UploadFile(file=buf, filename="img.jpg", headers=headers)

    with pytest.raises(HTTPException) as exc:
        await images_api.upload_image(file=upload, compression_type="bad")

    assert exc.value.status_code == 400
    assert "compression" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_compress_image_rejects_excessive_pixel_count(monkeypatch) -> None:
    from app.services.image_service import MAX_TOTAL_PIXELS, ImageService

    class FakeLargeImage:
        mode = "RGB"
        width = MAX_TOTAL_PIXELS
        height = 2

        def thumbnail(self, *args, **kwargs):
            pass

    def fake_open(*args, **kwargs):
        return FakeLargeImage()

    monkeypatch.setattr("app.services.image_service.Image.open", fake_open)

    with pytest.raises(ValueError) as exc:
        await ImageService.compress_image(b"fake-data")

    assert "resolution" in str(exc.value).lower()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
