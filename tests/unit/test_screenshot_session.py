"""Unit tests for ScreenshotSession application service."""

import io
from pathlib import Path
from PIL import Image
import pytest

from eprep.application.screenshot_session import ScreenshotSession
from eprep.domain.exceptions import DuplicateImageError, SessionCapacityError
from eprep.domain.models import ScreenshotItem
from eprep.infrastructure.imaging.processor import ImageLoader


def make_dummy_item(name: str, color: tuple[int, int, int] = (255, 0, 0)) -> ScreenshotItem:
    """Create a dummy ScreenshotItem with unique pixel content."""
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color=color)
    img.save(buf, format="PNG")
    return ImageLoader.load_from_bytes(buf.getvalue(), name=name)


def test_empty_session():
    """Test 1: Empty session starts with 0 items."""
    session = ScreenshotSession()
    assert session.count == 0
    assert session.is_empty
    assert not session.is_full
    assert len(session.items) == 0


def test_add_single_image():
    """Test 2: Add 1 valid image."""
    session = ScreenshotSession()
    item = make_dummy_item("pic1.png", (10, 20, 30))
    session.add_item(item)

    assert session.count == 1
    assert not session.is_empty
    assert session.items[0].name == "pic1.png"


def test_add_five_images_reaches_capacity():
    """Test 3: Add exactly 5 images."""
    session = ScreenshotSession()
    for i in range(5):
        session.add_item(make_dummy_item(f"pic_{i}.png", (i * 10, i * 20, i * 30)))

    assert session.count == 5
    assert session.is_full


def test_attempt_sixth_image_rejected():
    """Test 4: Attempting sixth image raises SessionCapacityError and preserves count."""
    session = ScreenshotSession()
    for i in range(5):
        session.add_item(make_dummy_item(f"pic_{i}.png", (i * 10, i * 20, i * 30)))

    sixth = make_dummy_item("pic_extra.png", (100, 100, 100))
    with pytest.raises(SessionCapacityError, match="Maximum of 5 screenshots reached"):
        session.add_item(sixth)

    assert session.count == 5


def test_remove_individual_screenshot():
    """Test 5: Remove one screenshot, verifying remaining count and preserved order."""
    session = ScreenshotSession()
    items = [make_dummy_item(f"pic_{i}.png", (i * 20, 50, 50)) for i in range(5)]
    for it in items:
        session.add_item(it)

    # Remove the 3rd item (index 2)
    to_remove = items[2]
    removed = session.remove_item(to_remove.id)

    assert removed is True
    assert session.count == 4
    remaining_names = [it.name for it in session.items]
    assert remaining_names == ["pic_0.png", "pic_1.png", "pic_3.png", "pic_4.png"]


def test_clear_session():
    """Test 6: Clear session resets to empty."""
    session = ScreenshotSession()
    session.add_item(make_dummy_item("pic_1.png", (1, 2, 3)))
    session.add_item(make_dummy_item("pic_2.png", (4, 5, 6)))
    assert session.count == 2

    session.clear()
    assert session.count == 0
    assert session.is_empty
    assert len(session.items) == 0


def test_exact_duplicate_rejected():
    """Test 7: Exact duplicate does not consume another slot and raises DuplicateImageError."""
    session = ScreenshotSession()
    item1 = make_dummy_item("first.png", (50, 50, 50))
    session.add_item(item1)

    # Create an identical image item with different name
    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color=(50, 50, 50))
    img.save(buf, format="PNG")
    dup_item = ImageLoader.load_from_bytes(buf.getvalue(), name="duplicate.png")

    with pytest.raises(DuplicateImageError, match="already added"):
        session.add_item(dup_item)

    assert session.count == 1


def test_batch_add_paths(tmp_path: Path):
    """Verify batch addition with mixed valid, duplicate, and limit enforcement."""
    session = ScreenshotSession()

    # Create 3 valid files
    f1 = tmp_path / "img1.png"
    f2 = tmp_path / "img2.jpg"
    f3 = tmp_path / "img3.webp"
    f1.write_bytes(make_dummy_item("1", (10, 0, 0)).image_bytes)
    f2.write_bytes(make_dummy_item("2", (20, 0, 0)).image_bytes)
    f3.write_bytes(make_dummy_item("3", (30, 0, 0)).image_bytes)

    # Unsupported file
    f_bad = tmp_path / "notes.txt"
    f_bad.write_text("not an image")

    # Add 3 valid + 1 bad + duplicate of 1
    result = session.add_multiple_paths([f1, f2, f3, f_bad, f1])

    assert len(result.added) == 3
    assert len(result.rejected_unsupported) == 1
    assert len(result.rejected_duplicate) == 1
    assert session.count == 3
    assert "3 screenshots added." in result.status_message
    assert "unsupported" in result.status_message
