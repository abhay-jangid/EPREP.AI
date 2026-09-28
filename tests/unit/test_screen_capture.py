"""Unit tests for Phase 5 screen capture, geometry normalization, DPI scaling, and session integration."""

import io
from PIL import Image
import pytest
from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication

from eprep.domain.exceptions import ImageValidationError, ScreenCaptureError
from eprep.domain.models import ScreenshotSource
from eprep.infrastructure.imaging.capture import (
    clamp_rect_to_bounds,
    crop_image_bytes,
    crop_pixmap_to_png_bytes,
    is_valid_selection,
    normalize_selection,
    scale_coordinates_to_device,
)
from eprep.ui.main_window import MainWindow
from eprep.ui.overlay import CaptureManager


@pytest.fixture
def app():
    """Ensure a QApplication instance is initialized for GUI tests."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def main_window(app):
    """Provide a fresh MainWindow instance."""
    window = MainWindow()
    yield window
    window.close()


# ---------------------------------------------------------------------------
# 1. Selection Geometry Normalization Tests (Section 33)
# ---------------------------------------------------------------------------


def test_normalize_selection_all_four_directions():
    """Verify dragging in all four Cartesian directions produces identical normalized rectangles."""
    # Top-Left to Bottom-Right
    x, y, w, h = normalize_selection(10, 20, 110, 80)
    assert (x, y, w, h) == (10, 20, 100, 60)

    # Bottom-Right to Top-Left
    x, y, w, h = normalize_selection(110, 80, 10, 20)
    assert (x, y, w, h) == (10, 20, 100, 60)

    # Top-Right to Bottom-Left
    x, y, w, h = normalize_selection(110, 20, 10, 80)
    assert (x, y, w, h) == (10, 20, 100, 60)

    # Bottom-Left to Top-Right
    x, y, w, h = normalize_selection(10, 80, 110, 20)
    assert (x, y, w, h) == (10, 20, 100, 60)


def test_normalize_selection_zero_delta():
    """Verify click without drag produces zero width and height."""
    x, y, w, h = normalize_selection(50, 50, 50, 50)
    assert (x, y, w, h) == (50, 50, 0, 0)


def test_is_valid_selection_threshold():
    """Verify rejection of empty, tiny, or negative selections."""
    assert is_valid_selection(8, 8)
    assert is_valid_selection(100, 50)
    assert not is_valid_selection(7, 8)
    assert not is_valid_selection(8, 7)
    assert not is_valid_selection(0, 0)
    assert not is_valid_selection(-10, 50)


def test_clamp_rect_to_bounds():
    """Verify rectangle clamping within bounding limits."""
    # Fully inside
    assert clamp_rect_to_bounds(10, 10, 50, 50, 100, 100) == (10, 10, 50, 50)

    # Exceeding right / bottom
    assert clamp_rect_to_bounds(80, 80, 50, 50, 100, 100) == (80, 80, 20, 20)

    # Negative origin
    assert clamp_rect_to_bounds(-10, -5, 50, 50, 100, 100) == (0, 0, 50, 50)


# ---------------------------------------------------------------------------
# 2. High-DPI Coordinate Scaling Tests (Section 37)
# ---------------------------------------------------------------------------


def test_scale_coordinates_to_device_dpr_1_0():
    """Verify 100% display scaling (DPR 1.0) maps coordinates 1:1."""
    dx, dy, dw, dh = scale_coordinates_to_device(100, 50, 200, 150, dpr=1.0)
    assert (dx, dy, dw, dh) == (100, 50, 200, 150)


def test_scale_coordinates_to_device_dpr_1_25():
    """Verify 125% display scaling (DPR 1.25) scales coordinates correctly."""
    dx, dy, dw, dh = scale_coordinates_to_device(100, 50, 200, 150, dpr=1.25)
    assert (dx, dy, dw, dh) == (125, 62, 250, 188)


def test_scale_coordinates_to_device_dpr_1_5():
    """Verify 150% display scaling (DPR 1.5) scales coordinates correctly."""
    dx, dy, dw, dh = scale_coordinates_to_device(100, 50, 200, 150, dpr=1.5)
    assert (dx, dy, dw, dh) == (150, 75, 300, 225)


def test_scale_coordinates_to_device_dpr_2_0():
    """Verify 200% display scaling (DPR 2.0) scales coordinates correctly."""
    dx, dy, dw, dh = scale_coordinates_to_device(100, 50, 200, 150, dpr=2.0)
    assert (dx, dy, dw, dh) == (200, 100, 400, 300)


def test_scale_coordinates_with_max_bounds_clamping():
    """Verify coordinates are clamped to physical backing image bounds."""
    dx, dy, dw, dh = scale_coordinates_to_device(
        150, 150, 200, 200, dpr=1.5, max_width=400, max_height=300
    )
    assert dx == 225
    assert dy == 225
    assert dx + dw <= 400
    assert dy + dh <= 300


# ---------------------------------------------------------------------------
# 3. Crop Tests with Synthetic Images (Section 34)
# ---------------------------------------------------------------------------


def test_crop_image_bytes_synthetic():
    """Verify cropping an in-memory synthetic image produces exact dimensions and content."""
    # Create 200x200 synthetic image with 4 color quadrants
    # TL: Red (255, 0, 0), TR: Green (0, 255, 0), BL: Blue (0, 0, 255), BR: Yellow (255, 255, 0)
    base_img = Image.new("RGB", (200, 200))
    for x in range(200):
        for y in range(200):
            if x < 100 and y < 100:
                base_img.putpixel((x, y), (255, 0, 0))
            elif x >= 100 and y < 100:
                base_img.putpixel((x, y), (0, 255, 0))
            elif x < 100 and y >= 100:
                base_img.putpixel((x, y), (0, 0, 255))
            else:
                base_img.putpixel((x, y), (255, 255, 0))

    buf = io.BytesIO()
    base_img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # Crop the bottom-right yellow quadrant: (100, 100, 50, 50)
    cropped_bytes = crop_image_bytes(png_bytes, (100, 100, 50, 50))
    with Image.open(io.BytesIO(cropped_bytes)) as cropped:
        assert cropped.size == (50, 50)
        assert cropped.format == "PNG"
        # Verify color is yellow
        assert cropped.getpixel((0, 0)) == (255, 255, 0)
        assert cropped.getpixel((49, 49)) == (255, 255, 0)


def test_crop_image_bytes_rejects_invalid_dimensions():
    """Verify crop raises ImageValidationError for invalid dimensions."""
    base_img = Image.new("RGB", (100, 100), color=(10, 20, 30))
    buf = io.BytesIO()
    base_img.save(buf, format="PNG")
    data = buf.getvalue()

    with pytest.raises(ImageValidationError):
        crop_image_bytes(data, (0, 0, 0, 0))

    with pytest.raises(ImageValidationError):
        crop_image_bytes(data, (0, 0, -10, 50))

    with pytest.raises(ImageValidationError):
        crop_image_bytes(data, (150, 150, 20, 20))


def test_crop_pixmap_to_png_bytes(app):
    """Verify QPixmap cropping and encoding to PNG bytes with DPR support."""
    pixmap = QPixmap(300, 200)
    pixmap.fill(QColor(100, 150, 200))

    # Crop with DPR 1.0
    png_bytes = crop_pixmap_to_png_bytes(pixmap, 10, 20, 80, 60, dpr=1.0)
    with Image.open(io.BytesIO(png_bytes)) as img:
        assert img.size == (80, 60)
        assert img.format == "PNG"

    # Crop with DPR 1.5 -> device pixels 80*1.5=120, 60*1.5=90
    png_bytes_hi = crop_pixmap_to_png_bytes(pixmap, 10, 20, 80, 60, dpr=1.5)
    with Image.open(io.BytesIO(png_bytes_hi)) as img:
        assert img.size == (120, 90)


def test_crop_pixmap_null_pixmap_raises():
    """Verify null pixmap raises ScreenCaptureError."""
    null_pix = QPixmap()
    with pytest.raises(ScreenCaptureError):
        crop_pixmap_to_png_bytes(null_pix, 0, 0, 50, 50, dpr=1.0)


# ---------------------------------------------------------------------------
# 4. Capture Integration & Session Tests (Section 35)
# ---------------------------------------------------------------------------


def create_synthetic_crop_bytes(w: int = 120, h: int = 80, color: tuple = (30, 60, 90)) -> bytes:
    """Helper to generate in-memory synthetic PNG bytes."""
    img = Image.new("RGB", (w, h), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_capture_integration_session_increment(main_window):
    """Verify completing a capture adds a ScreenshotItem with source SCREEN_CAPTURE."""
    panel = main_window.screenshot_panel
    assert panel.session.count == 0

    png_data = create_synthetic_crop_bytes(160, 90, (50, 80, 120))
    panel._on_capture_completed(png_data, "Screen Capture")

    assert panel.session.count == 1
    assert panel.count_label_text == "1 / 5"
    assert not panel.is_empty

    item = panel.session.items[0]
    assert item.name == "Screen Capture 1"
    assert item.source_type == ScreenshotSource.SCREEN_CAPTURE.value
    assert item.width == 160
    assert item.height == 90
    assert item.format == "PNG"
    assert panel.capture_button.isEnabled()


def test_capture_integration_duplicate_rejected(main_window):
    """Verify adding an exact duplicate capture does not increment count."""
    panel = main_window.screenshot_panel
    png_data = create_synthetic_crop_bytes(100, 100, (10, 20, 30))

    panel._on_capture_completed(png_data, "Screen Capture")
    assert panel.session.count == 1

    # Attempt to add identical data
    panel._on_capture_completed(png_data, "Screen Capture")
    assert panel.session.count == 1
    assert panel.count_label_text == "1 / 5"


def test_capture_integration_capacity_blocks_new_capture(main_window):
    """Verify capture button and clicked handler enforce 5/5 capacity."""
    panel = main_window.screenshot_panel

    for i in range(5):
        data = create_synthetic_crop_bytes(80, 80, (i * 30, 0, 0))
        panel._on_capture_completed(data, f"Screen Capture {i+1}")

    assert panel.session.count == 5
    assert panel.count_label_text == "5 / 5"
    assert not panel.capture_button.isEnabled()

    # Calling clicked handler at capacity emits status and aborts
    status_messages = []
    panel.status_message_emitted.connect(status_messages.append)
    panel._on_capture_clicked()

    assert not panel.capture_manager.is_active
    assert "Maximum of 5 screenshots reached." in status_messages


def test_capture_integration_cancellation_preserves_session(main_window):
    """Verify cancellation leaves active session untouched."""
    panel = main_window.screenshot_panel
    png_data = create_synthetic_crop_bytes(100, 100, (10, 20, 30))
    panel._on_capture_completed(png_data, "Screen Capture")
    assert panel.session.count == 1

    status_messages = []
    panel.status_message_emitted.connect(status_messages.append)

    panel._on_capture_cancelled()
    assert panel.session.count == 1
    assert panel.count_label_text == "1 / 5"
    assert "Screen capture cancelled." in status_messages


# ---------------------------------------------------------------------------
# 5. UI State & Re-entrancy Tests (Section 25 & 36)
# ---------------------------------------------------------------------------


def test_reentrancy_guard_blocks_concurrent_capture(main_window):
    """Verify duplicate capture requests are safely ignored while capture is active."""
    panel = main_window.screenshot_panel

    manager = panel.capture_manager
    assert not manager.is_active

    # Mock screen acquisition to keep overlay open
    fake_pixmap = QPixmap(200, 200)
    fake_pixmap.fill(QColor("blue"))

    # Start capture with delay=0 for instant execution
    started = manager.start_capture(target_window=main_window, delay_ms=0)
    assert started
    assert manager.is_active

    # Secondary attempt must be rejected
    second_started = manager.start_capture(target_window=main_window, delay_ms=0)
    assert not second_started

    # Cancel and verify reset
    manager._on_cancelled()
    assert not manager.is_active
    assert not manager._overlays


def test_capture_screen_button_cycle_0_to_5(main_window):
    """Verify button cycle: 0/5 enabled -> 5/5 disabled -> remove -> 4/5 enabled."""
    panel = main_window.screenshot_panel

    # Initial state: 0/5 -> enabled
    assert panel.capture_button.isEnabled()

    # Add 5 captures
    for i in range(5):
        data = create_synthetic_crop_bytes(50, 50, (i * 25, i * 25, 0))
        panel._on_capture_completed(data, "Capture")

    assert panel.session.count == 5
    assert not panel.capture_button.isEnabled()

    # Remove one item
    item_id = panel.session.items[0].id
    panel._on_remove_clicked(item_id)

    assert panel.session.count == 4
    assert panel.capture_button.isEnabled()
