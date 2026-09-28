"""UI foundation tests for EPREP.AI."""

import os
import pytest
from PySide6.QtWidgets import QApplication

from eprep import __app_name__
from eprep.domain.language import SupportedLanguage
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


def test_main_window_instantiation(main_window):
    """Test 1: MainWindow can be instantiated under a QApplication."""
    assert main_window is not None
    assert isinstance(main_window, MainWindow)


def test_main_window_title(main_window):
    """Test 2: Window title is EPREP.AI."""
    assert main_window.windowTitle() == __app_name__
    assert main_window.windowTitle() == "EPREP.AI"


def test_language_selector_languages(main_window):
    """Test 3: Language selector contains exactly six approved languages."""
    available = main_window.language_selector.available_languages()
    assert len(available) == 6
    expected_values = {"Python", "Java", "C", "C++", "JavaScript", "TypeScript"}
    assert {lang.value for lang in available} == expected_values


def test_language_selector_default_python(main_window):
    """Test 4: Python is initially selected."""
    assert main_window.language_selector.current_language() == SupportedLanguage.PYTHON


def test_analyze_button_initially_disabled(main_window):
    """Test 5: Analyze Problem is initially disabled."""
    assert not main_window.analyze_button.isEnabled()


def test_screenshot_panel_initial_count(main_window):
    """Test 6: Screenshot count initially shows 0 / 5."""
    assert main_window.screenshot_panel.count_label_text == "0 / 5"
    assert main_window.screenshot_panel.is_empty


def test_solution_panel_initially_empty_and_readonly(main_window):
    """Test 7: Code/solution area is initially read-only and empty."""
    assert main_window.solution_panel.is_code_read_only
    assert main_window.solution_panel.is_code_empty


def test_language_selection_change(main_window):
    """Verify changing language selection updates the widget correctly."""
    events = []
    main_window.language_selector.language_changed.connect(events.append)

    main_window.language_selector.set_language(SupportedLanguage.CPP)
    assert main_window.language_selector.current_language() == SupportedLanguage.CPP
    assert len(events) == 1
    assert events[0] == SupportedLanguage.CPP


def test_control_bar_labels_and_status(main_window):
    """Verify output mode, typing status, and status bar initial states."""
    assert "Safe Paste" in main_window.output_mode_label.text()
    assert "Not Ready to Type" in main_window.typing_status_label.text()
    assert main_window.statusBar().currentMessage() == "Ready"


def test_window_minimum_size(main_window):
    """Verify window has reasonable minimum size preventing control collapse."""
    assert main_window.minimumWidth() >= 800
    assert main_window.minimumHeight() >= 500
