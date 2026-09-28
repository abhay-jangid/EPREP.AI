"""Solution workspace panel widget."""

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SolutionPanel(QWidget):
    """Panel displaying problem analysis, explanation, and generated code."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_label = QLabel("Solution Workspace", self)
        header_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #f1f5f9;")
        layout.addWidget(header_label)

        # Tabs
        self._tab_widget = QTabWidget(self)

        # Tab 1: Analysis & Explanation
        self._analysis_edit = QPlainTextEdit(self)
        self._analysis_edit.setReadOnly(True)
        self._analysis_edit.setPlaceholderText(
            "Waiting for a problem...\n\n"
            "Add screenshots of your programming question and click 'Analyze Problem' "
            "to generate an explanation and code solution."
        )

        # Tab 2: Generated Code
        self._code_edit = QPlainTextEdit(self)
        self._code_edit.setReadOnly(True)
        self._code_edit.setPlaceholderText(
            "// Approved code will be displayed here.\n"
            "// Waiting for a problem..."
        )

        # Apply system monospaced font to code editor
        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_font.setPointSize(10)
        self._code_edit.setFont(fixed_font)

        self._tab_widget.addTab(self._analysis_edit, "Problem Analysis")
        self._tab_widget.addTab(self._code_edit, "Generated Code")

        layout.addWidget(self._tab_widget, 1)

    @property
    def code_edit(self) -> QPlainTextEdit:
        """Return the code editor widget."""
        return self._code_edit

    @property
    def analysis_edit(self) -> QPlainTextEdit:
        """Return the analysis editor widget."""
        return self._analysis_edit

    @property
    def is_code_empty(self) -> bool:
        """Check if generated code is empty."""
        return len(self._code_edit.toPlainText().strip()) == 0

    @property
    def is_code_read_only(self) -> bool:
        """Check if code editor is read-only."""
        return self._code_edit.isReadOnly()
