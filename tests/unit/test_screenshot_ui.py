"""UI integration tests for ScreenshotPanel and session interaction."""

import io
import os
from pathlib import Path
from PIL import Image
import pytest
from PySide6.QtWidgets import QApplication

from eprep.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Create a headless QApplication instance for tests."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication(["--platform", "offscreen"])
    yield app


@pytest.fixture
def main_window(qapp):
    """Create a MainWindow instance for testing."""
    window = MainWindow()
    yield window
    window.close()


def create_sample_image(tmp_path: Path, filename: str, color=(100, 150, 200)) -> Path:
    """Generate a test image file on disk."""
    path = tmp_path / filename
    buf = io.BytesIO()
    img = Image.new("RGB", (80, 80), color=color)
    img.save(buf, format="PNG")
    path.write_bytes(buf.getvalue())
    return path


def test_initial_button_states(main_window):
    """Verify initial button enabled states."""
    panel = main_window.screenshot_panel

    assert panel.add_button.isEnabled()
    assert panel.capture_button.isEnabled()
    assert not panel.clear_button.isEnabled()
    assert panel.count_label_text == "0 / 5"
    assert panel.is_empty


def test_add_screenshot_updates_ui(main_window, tmp_path: Path):
    """Verify adding an image updates the count and enables clear button."""
    panel = main_window.screenshot_panel
    img_path = create_sample_image(tmp_path, "test1.png", (10, 20, 30))

    panel.add_paths([img_path])

    assert panel.count_label_text == "1 / 5"
    assert not panel.is_empty
    assert panel.clear_button.isEnabled()
    assert panel.add_button.isEnabled()


def test_capacity_disables_add_button(main_window, tmp_path: Path):
    """Verify reaching 5 screenshots disables the Add and Capture buttons."""
    panel = main_window.screenshot_panel
    paths = [create_sample_image(tmp_path, f"img_{i}.png", (i * 20, 0, 0)) for i in range(5)]

    panel.add_paths(paths)

    assert panel.count_label_text == "5 / 5"
    assert not panel.add_button.isEnabled()
    assert not panel.capture_button.isEnabled()
    assert panel.clear_button.isEnabled()

    # Remove one item
    first_item_id = panel.session.items[0].id
    panel._on_remove_clicked(first_item_id)

    assert panel.count_label_text == "4 / 5"
    assert panel.add_button.isEnabled()
    assert panel.capture_button.isEnabled()


def test_clear_button_resets_ui(main_window, tmp_path: Path):
    """Verify clear button empties the panel and resets controls."""
    panel = main_window.screenshot_panel
    p1 = create_sample_image(tmp_path, "a.png", (1, 2, 3))
    p2 = create_sample_image(tmp_path, "b.png", (4, 5, 6))

    panel.add_paths([p1, p2])
    assert panel.count_label_text == "2 / 5"

    panel._on_clear_clicked()
    assert panel.count_label_text == "0 / 5"
    assert panel.is_empty
    assert not panel.clear_button.isEnabled()
    assert panel.add_button.isEnabled()
    assert panel.capture_button.isEnabled()


def test_analyze_button_remains_disabled_with_screenshots(main_window, tmp_path: Path):
    """Verify Analyze Problem remains disabled in Phase 4 even after adding images."""
    panel = main_window.screenshot_panel
    p1 = create_sample_image(tmp_path, "problem.png", (50, 100, 150))

    panel.add_paths([p1])
    assert panel.count_label_text == "1 / 5"
    assert not main_window.analyze_button.isEnabled()
