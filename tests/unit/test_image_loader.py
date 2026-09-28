"""Unit tests for ImageLoader and image validation."""

import io
from pathlib import Path
from PIL import Image
import pytest

from eprep.domain.exceptions import ImageValidationError
from eprep.infrastructure.imaging.processor import ImageLoader


def create_test_image_bytes(format_name: str, size: tuple[int, int] = (100, 100)) -> bytes:
    """Helper creating valid in-memory image bytes."""
    buf = io.BytesIO()
    # JPEG does not support RGBA mode
    mode = "RGB" if format_name.upper() in {"JPEG", "JPG"} else "RGBA"
    img = Image.new(mode, size, color=(50, 100, 150))
    img.save(buf, format=format_name)
    return buf.getvalue()


def test_load_valid_png():
    """Verify loading valid PNG bytes."""
    data = create_test_image_bytes("PNG", (120, 80))
    item = ImageLoader.load_from_bytes(data, name="test.png")
    assert item.name == "test.png"
    assert item.format == "PNG"
    assert item.width == 120
    assert item.height == 80
    assert len(item.content_hash) == 64
    assert item.image_bytes == data


def test_load_valid_jpeg():
    """Verify loading valid JPEG bytes."""
    data = create_test_image_bytes("JPEG", (200, 150))
    item = ImageLoader.load_from_bytes(data, name="test.jpg")
    assert item.format == "JPEG"
    assert item.width == 200
    assert item.height == 150


def test_load_valid_webp():
    """Verify loading valid WebP bytes."""
    data = create_test_image_bytes("WEBP", (64, 64))
    item = ImageLoader.load_from_bytes(data, name="test.webp")
    assert item.format == "WEBP"
    assert item.width == 64
    assert item.height == 64


def test_load_from_path(tmp_path: Path):
    """Verify loading image from a valid file path."""
    file_path = tmp_path / "sample.png"
    file_path.write_bytes(create_test_image_bytes("PNG", (50, 50)))

    item = ImageLoader.load_from_path(file_path)
    assert item.name == "sample.png"
    assert item.width == 50
    assert item.height == 50


def test_unsupported_format_rejected():
    """Verify unsupported image formats (e.g. BMP, GIF) are rejected."""
    buf = io.BytesIO()
    img = Image.new("RGB", (30, 30), color="red")
    img.save(buf, format="BMP")
    bmp_bytes = buf.getvalue()

    with pytest.raises(ImageValidationError, match="Unsupported format"):
        ImageLoader.load_from_bytes(bmp_bytes, name="test.bmp")


def test_corrupt_image_rejected():
    """Verify corrupted / truncated image bytes raise ImageValidationError."""
    corrupt_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtruncatedcorruptbytes"
    with pytest.raises(ImageValidationError):
        ImageLoader.load_from_bytes(corrupt_bytes, name="corrupt.png")


def test_nonexistent_file_rejected(tmp_path: Path):
    """Verify attempting to load a non-existent file path raises ImageValidationError."""
    non_existent = tmp_path / "ghost.png"
    with pytest.raises(ImageValidationError, match="File not found"):
        ImageLoader.load_from_path(non_existent)


def test_directory_path_rejected(tmp_path: Path):
    """Verify directory paths are rejected."""
    with pytest.raises(ImageValidationError, match="Directory drop is not supported"):
        ImageLoader.load_from_path(tmp_path)


def test_empty_bytes_rejected():
    """Verify empty byte stream is rejected."""
    with pytest.raises(ImageValidationError, match="empty"):
        ImageLoader.load_from_bytes(b"", name="empty.png")
