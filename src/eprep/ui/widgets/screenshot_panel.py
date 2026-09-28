"""Screenshot management panel widget."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ScreenshotPanel(QWidget):
    """Panel displaying screenshot list and capture controls."""

    MAX_SCREENSHOTS = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._count = 0
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header with title and count
        header_layout = QHBoxLayout()
        self._title_label = QLabel("Screenshots", self)
        self._title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #f1f5f9;")

        self._count_label = QLabel(f"{self._count} / {self.MAX_SCREENSHOTS}", self)
        self._count_label.setStyleSheet(
            "background-color: #1e293b; color: #cbd5e1; border: 1px solid #334155; "
            "font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 10px;"
        )

        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        header_layout.addWidget(self._count_label)
        main_layout.addLayout(header_layout)

        # Empty display area / thumbnail placeholder
        self._display_frame = QFrame(self)
        self._display_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._display_frame.setStyleSheet(
            "QFrame { border: 2px dashed #334155; border-radius: 8px; background-color: #0b0f19; }"
        )

        display_layout = QVBoxLayout(self._display_frame)
        display_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._empty_label = QLabel(
            "No screenshots added\n\nUpload or capture up to 5 screenshots of a problem.",
            self._display_frame,
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        display_layout.addWidget(self._empty_label)

        main_layout.addWidget(self._display_frame, 1)

        # Controls
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self._add_btn = QPushButton("Add Screenshot", self)
        self._add_btn.setEnabled(False)
        self._add_btn.setToolTip("Image upload will be available in Phase 4")

        self._capture_btn = QPushButton("Capture Screen", self)
        self._capture_btn.setEnabled(False)
        self._capture_btn.setToolTip("Screen snipping will be available in Phase 5")

        self._clear_btn = QPushButton("Clear", self)
        self._clear_btn.setEnabled(False)

        button_layout.addWidget(self._add_btn)
        button_layout.addWidget(self._capture_btn)
        button_layout.addWidget(self._clear_btn)
        main_layout.addLayout(button_layout)

    @property
    def count_label_text(self) -> str:
        """Return the text of the count label."""
        return self._count_label.text()

    @property
    def is_empty(self) -> bool:
        """Check if screenshot panel is empty."""
        return self._count == 0

    @property
    def add_button(self) -> QPushButton:
        """Return the add screenshot button."""
        return self._add_btn

    @property
    def capture_button(self) -> QPushButton:
        """Return the capture screen button."""
        return self._capture_btn

    @property
    def clear_button(self) -> QPushButton:
        """Return the clear button."""
        return self._clear_btn
