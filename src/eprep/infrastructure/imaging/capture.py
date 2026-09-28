"""Screen capture geometry, coordinate scaling, and in-memory image cropping."""

import io
from PIL import Image
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QPixmap

from eprep.domain.exceptions import ImageValidationError, ScreenCaptureError


MIN_SELECTION_SIZE: int = 8


def normalize_selection(x1: int, y1: int, x2: int, y2: int) -> tuple[int, int, int, int]:
    """Normalize two drag points into (x, y, width, height) with non-negative dimensions."""
    x = min(x1, x2)
    y = min(y1, y2)
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    return x, y, w, h


def is_valid_selection(
    w: int,
    h: int,
    min_width: int = MIN_SELECTION_SIZE,
    min_height: int = MIN_SELECTION_SIZE,
) -> bool:
    """Determine whether selection dimensions meet the minimum required size."""
    return w >= min_width and h >= min_height


def clamp_rect_to_bounds(
    x: int,
    y: int,
    w: int,
    h: int,
    max_w: int,
    max_h: int,
) -> tuple[int, int, int, int]:
    """Clamp a rectangle within given 0-indexed maximum boundary dimensions."""
    clamped_x = max(0, min(x, max_w - 1))
    clamped_y = max(0, min(y, max_h - 1))
    clamped_w = min(w, max_w - clamped_x)
    clamped_h = min(h, max_h - clamped_y)
    return clamped_x, clamped_y, max(0, clamped_w), max(0, clamped_h)


def scale_coordinates_to_device(
    x: int,
    y: int,
    w: int,
    h: int,
    dpr: float,
    max_width: int | None = None,
    max_height: int | None = None,
) -> tuple[int, int, int, int]:
    """Convert logical screen coordinates to physical device pixel coordinates."""
    if dpr <= 0:
        dpr = 1.0

    dx = int(round(x * dpr))
    dy = int(round(y * dpr))
    dw = int(round(w * dpr))
    dh = int(round(h * dpr))

    if w > 0 and dw <= 0:
        dw = 1
    if h > 0 and dh <= 0:
        dh = 1

    if max_width is not None and max_width > 0:
        dx = max(0, min(dx, max_width - 1))
        dw = max(1, min(dw, max_width - dx))
    if max_height is not None and max_height > 0:
        dy = max(0, min(dy, max_height - 1))
        dh = max(1, min(dh, max_height - dy))

    return dx, dy, dw, dh


def crop_image_bytes(
    image_bytes: bytes,
    crop_box: tuple[int, int, int, int],
) -> bytes:
    """Crop an in-memory image using (x, y, width, height) and return encoded PNG bytes.

    Raises:
        ImageValidationError: If crop coordinates are invalid or image is unreadable.
    """
    x, y, w, h = crop_box
    if w <= 0 or h <= 0:
        raise ImageValidationError(f"Invalid crop dimensions: width={w}, height={h}")

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img_w, img_h = img.size
            if x < 0 or y < 0 or x >= img_w or y >= img_h:
                raise ImageValidationError(
                    f"Crop origin ({x}, {y}) out of image bounds ({img_w}x{img_h})"
                )

            right = min(x + w, img_w)
            lower = min(y + h, img_h)
            cropped = img.crop((x, y, right, lower))

            out_buf = io.BytesIO()
            cropped.save(out_buf, format="PNG")
            return out_buf.getvalue()
    except ImageValidationError:
        raise
    except Exception as exc:
        raise ImageValidationError(f"Failed to crop image bytes: {exc}") from exc


def crop_pixmap_to_png_bytes(
    pixmap: QPixmap,
    logical_x: int,
    logical_y: int,
    logical_w: int,
    logical_h: int,
    dpr: float,
) -> bytes:
    """Crop a captured QPixmap using logical coordinates and device pixel ratio into PNG bytes.

    Raises:
        ScreenCaptureError: If the pixmap is invalid or cropping/encoding fails.
    """
    if pixmap.isNull():
        raise ScreenCaptureError("Cannot crop from a null or invalid screen pixmap.")

    dx, dy, dw, dh = scale_coordinates_to_device(
        logical_x,
        logical_y,
        logical_w,
        logical_h,
        dpr,
        max_width=pixmap.width(),
        max_height=pixmap.height(),
    )

    if dw <= 0 or dh <= 0:
        raise ScreenCaptureError(f"Invalid cropped dimensions: width={dw}, height={dh}")

    sub_pixmap = pixmap.copy(dx, dy, dw, dh)
    if sub_pixmap.isNull():
        raise ScreenCaptureError("Failed to extract cropped pixmap from screen capture.")

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not sub_pixmap.save(buffer, "PNG"):
        raise ScreenCaptureError("Failed to encode cropped screen pixmap to PNG.")

    return bytes(buffer.data())
