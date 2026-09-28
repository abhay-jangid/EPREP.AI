"""Image loading, format validation, and integrity verification using Pillow."""

import hashlib
import io
from pathlib import Path
import uuid
from PIL import Image, UnidentifiedImageError

from eprep.domain.exceptions import ImageValidationError
from eprep.domain.models import ScreenshotItem

SUPPORTED_IMAGE_FORMATS: frozenset[str] = frozenset({"PNG", "JPEG", "JPG", "WEBP"})


class ImageLoader:
    """Validates and loads images into memory-first ScreenshotItem representations."""

    @classmethod
    def load_from_path(cls, file_path: Path | str) -> ScreenshotItem:
        """Load and validate an image from a file path."""
        path = Path(file_path)

        if not path.exists():
            raise ImageValidationError(f"File not found: {path.name}")

        if path.is_dir():
            raise ImageValidationError(f"Directory drop is not supported: {path.name}")

        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            raise ImageValidationError(f"Could not read file {path.name}: {exc}") from exc

        return cls.load_from_bytes(raw_bytes, name=path.name, source_type="file")

    @classmethod
    def load_from_bytes(
        cls,
        data: bytes,
        name: str = "Screenshot",
        source_type: str = "file",
    ) -> ScreenshotItem:
        """Load and validate raw image bytes in memory."""
        if not data:
            raise ImageValidationError("Image data is empty.")

        try:
            with Image.open(io.BytesIO(data)) as img:
                img_format = (img.format or "").upper()
                if img_format not in SUPPORTED_IMAGE_FORMATS:
                    raise ImageValidationError(
                        f"Unsupported format '{img_format}'. Supported formats: PNG, JPEG, WebP."
                    )

                # Ensure pixel data is loaded to catch corruption or truncation
                img.load()
                width, height = img.size

                if width <= 0 or height <= 0:
                    raise ImageValidationError("Image dimensions must be greater than zero.")

        except UnidentifiedImageError as exc:
            raise ImageValidationError("File is not a valid or recognizable image.") from exc
        except (OSError, SyntaxError) as exc:
            raise ImageValidationError(f"Corrupt or truncated image file: {exc}") from exc

        content_hash = hashlib.sha256(data).hexdigest()
        item_id = str(uuid.uuid4())

        return ScreenshotItem(
            id=item_id,
            name=name,
            source_type=source_type,
            width=width,
            height=height,
            format=img_format,
            content_hash=content_hash,
            image_bytes=data,
        )
